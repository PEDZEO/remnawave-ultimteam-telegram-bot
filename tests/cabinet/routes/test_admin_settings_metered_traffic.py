from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.cabinet.routes import admin_settings
from app.cabinet.routes.admin_settings import (
    MeteredTrafficConfigurationUpdate,
    _serialize_exhausted_subscription,
)


SQUAD_UUID = '11111111-1111-1111-1111-111111111111'
METERED_NODE_UUID = '22222222-2222-2222-2222-222222222222'
UNLIMITED_NODE_UUID = '33333333-3333-3333-3333-333333333333'


class FakeApiContext(AbstractAsyncContextManager):
    def __init__(self, api: Any) -> None:
        self.api = api

    async def __aenter__(self) -> Any:
        return self.api

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        return None


class FakeDb:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    async def commit(self) -> None:
        self.events.append('commit')

    async def rollback(self) -> None:
        self.events.append('rollback')


def _payload(**overrides: Any) -> MeteredTrafficConfigurationUpdate:
    values = {
        'enabled': True,
        'squad_uuid': SQUAD_UUID,
        'metered_node_uuids': [METERED_NODE_UUID],
        'check_interval_seconds': 60,
        'warning_percent': 80,
        'server_label': 'Спецсерверы',
        'exhausted_message_ru': 'Использовано {used_gb} из {limit_gb} ГБ',
    }
    values.update(overrides)
    return MeteredTrafficConfigurationUpdate(**values)


def test_exhausted_subscription_payload_contains_admin_action_context() -> None:
    now = datetime.now(UTC)
    subscription = SimpleNamespace(
        id=22,
        user=SimpleNamespace(
            id=142,
            telegram_id=123456,
            username='pedzeo',
            email='admin@example.com',
            full_name='Admin User',
        ),
        tariff=SimpleNamespace(name='Стандарт + LTE'),
        traffic_limit_gb=35,
        traffic_used_gb=35.25,
        purchased_traffic_gb=10,
        metered_access_blocked_at=now,
        metered_traffic_last_checked_at=now,
        end_date=now + timedelta(days=20),
    )

    payload = _serialize_exhausted_subscription(subscription)

    assert payload.user_id == 142
    assert payload.subscription_id == 22
    assert payload.tariff_name == 'Стандарт + LTE'
    assert payload.traffic_limit_gb == 35
    assert payload.traffic_used_gb == 35.25
    assert payload.purchased_traffic_gb == 10
    assert payload.blocked_at == now


@pytest.mark.asyncio
async def test_configuration_updates_node_coefficients_before_starting_monitor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    saved_values: dict[str, Any] = {}
    squads = [SimpleNamespace(uuid=SQUAD_UUID, name='Metered', members_count=10, inbounds=[])]
    nodes = [
        SimpleNamespace(
            uuid=METERED_NODE_UUID,
            name='Metered node',
            address='metered.example',
            country_code='NL',
            is_connected=True,
            is_disabled=False,
            consumption_multiplier=0,
        ),
        SimpleNamespace(
            uuid=UNLIMITED_NODE_UUID,
            name='Unlimited node',
            address='unlimited.example',
            country_code='DE',
            is_connected=True,
            is_disabled=False,
            consumption_multiplier=1,
        ),
    ]

    class FakeApi:
        async def update_nodes_consumption_multiplier(self, uuids: list[str], multiplier: float) -> bool:
            events.append(f'node:{multiplier:g}:{",".join(uuids)}')
            return True

    class FakeRemnawaveService:
        def get_api_client(self) -> FakeApiContext:
            return FakeApiContext(FakeApi())

    class FakeMonitor:
        async def stop(self) -> None:
            events.append('stop')

        def is_enabled(self) -> bool:
            return True

        async def start(self) -> None:
            events.append('start')

    async def fake_load_topology() -> tuple[list[Any], list[Any]]:
        return squads, nodes

    async def fake_set_value(db: Any, key: str, value: Any) -> None:
        saved_values[key] = value
        events.append(f'setting:{key}')

    async def fake_configuration_payload(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {'nodes_updated': kwargs['nodes_updated']}

    monkeypatch.setattr(admin_settings, '_load_metered_topology', fake_load_topology)
    monkeypatch.setattr(admin_settings, 'remnawave_service', FakeRemnawaveService())
    monkeypatch.setattr(admin_settings, 'metered_traffic_service', FakeMonitor())
    monkeypatch.setattr(admin_settings.bot_configuration_service, 'set_value', fake_set_value)
    monkeypatch.setattr(admin_settings, '_metered_configuration_payload', fake_configuration_payload)

    response = await admin_settings.update_metered_traffic_configuration(
        _payload(),
        admin=SimpleNamespace(telegram_id=42),
        db=FakeDb(events),
    )

    assert response == {'nodes_updated': 2}
    assert events[0] == 'stop'
    assert events[1:3] == [
        f'node:1:{METERED_NODE_UUID}',
        f'node:0:{UNLIMITED_NODE_UUID}',
    ]
    assert events[-2:] == ['commit', 'start']
    assert saved_values['ULTIMA_METERED_SQUAD_UUID'] == SQUAD_UUID
    assert saved_values['ULTIMA_METERED_NODE_UUIDS'] == METERED_NODE_UUID
    assert saved_values['ULTIMA_METERED_TRAFFIC_ENABLED'] is True


@pytest.mark.asyncio
async def test_configuration_requires_metered_node_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    squads = [SimpleNamespace(uuid=SQUAD_UUID)]
    nodes = [SimpleNamespace(uuid=METERED_NODE_UUID)]

    async def fake_load_topology() -> tuple[list[Any], list[Any]]:
        return squads, nodes

    monkeypatch.setattr(admin_settings, '_load_metered_topology', fake_load_topology)

    with pytest.raises(HTTPException) as exc_info:
        await admin_settings.update_metered_traffic_configuration(
            _payload(metered_node_uuids=[]),
            admin=SimpleNamespace(telegram_id=42),
            db=FakeDb([]),
        )

    assert exc_info.value.status_code == 400
    assert 'хотя бы одну' in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_configuration_restores_coefficients_and_monitor_after_partial_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    squads = [SimpleNamespace(uuid=SQUAD_UUID)]
    nodes = [
        SimpleNamespace(uuid=METERED_NODE_UUID, consumption_multiplier=0),
        SimpleNamespace(uuid=UNLIMITED_NODE_UUID, consumption_multiplier=1),
    ]
    update_count = 0

    class FakeApi:
        async def update_nodes_consumption_multiplier(self, uuids: list[str], multiplier: float) -> bool:
            nonlocal update_count
            update_count += 1
            events.append(f'node:{multiplier:g}:{",".join(uuids)}')
            return update_count != 2

    class FakeRemnawaveService:
        def get_api_client(self) -> FakeApiContext:
            return FakeApiContext(FakeApi())

    class FakeMonitor:
        async def stop(self) -> None:
            events.append('stop')

        def is_enabled(self) -> bool:
            return True

        async def start(self) -> None:
            events.append('start')

    async def fake_load_topology() -> tuple[list[Any], list[Any]]:
        return squads, nodes

    monkeypatch.setattr(admin_settings, '_load_metered_topology', fake_load_topology)
    monkeypatch.setattr(admin_settings, 'remnawave_service', FakeRemnawaveService())
    monkeypatch.setattr(admin_settings, 'metered_traffic_service', FakeMonitor())

    with pytest.raises(HTTPException) as exc_info:
        await admin_settings.update_metered_traffic_configuration(
            _payload(),
            admin=SimpleNamespace(telegram_id=42),
            db=FakeDb(events),
        )

    assert exc_info.value.status_code == 502
    assert events == [
        'stop',
        f'node:1:{METERED_NODE_UUID}',
        f'node:0:{UNLIMITED_NODE_UUID}',
        'rollback',
        f'node:0:{METERED_NODE_UUID}',
        f'node:1:{UNLIMITED_NODE_UUID}',
        'start',
    ]
