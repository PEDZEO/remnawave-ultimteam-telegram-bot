from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.cabinet.routes import admin_settings
from app.cabinet.routes.admin_settings import (
    MeteredTrafficConfigurationUpdate,
    _metered_configuration_payload,
    _normalize_metered_squad_selection,
    _remove_retired_metered_squads,
    _serialize_exhausted_subscription,
)


SQUAD_UUID = '11111111-1111-1111-1111-111111111111'
SQUAD_UUID_2 = '11111111-1111-1111-1111-222222222222'
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

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=list))


def _payload(**overrides: Any) -> MeteredTrafficConfigurationUpdate:
    values = {
        'enabled': True,
        'squad_uuids': [SQUAD_UUID, SQUAD_UUID_2],
        'metered_node_uuids': [METERED_NODE_UUID],
        'metered_node_multipliers': {METERED_NODE_UUID: 2},
        'check_interval_seconds': 60,
        'warning_percent': 80,
        'server_label': 'Спецсерверы',
        'exhausted_message_ru': 'Использовано {used_gb} из {limit_gb} ГБ',
    }
    values.update(overrides)
    return MeteredTrafficConfigurationUpdate(**values)


def test_multiple_squads_are_normalized_and_legacy_single_value_still_works() -> None:
    assert _normalize_metered_squad_selection(_payload(squad_uuids=[SQUAD_UUID, SQUAD_UUID_2, SQUAD_UUID])) == [
        SQUAD_UUID,
        SQUAD_UUID_2,
    ]

    legacy_values = _payload().model_dump(exclude={'squad_uuids'})
    legacy_values['squad_uuid'] = SQUAD_UUID
    legacy_payload = MeteredTrafficConfigurationUpdate.model_validate(legacy_values)

    assert _normalize_metered_squad_selection(legacy_payload) == [SQUAD_UUID]


@pytest.mark.asyncio
async def test_retired_technical_squad_is_removed_from_stored_subscriptions() -> None:
    subscriptions = [
        SimpleNamespace(connected_squads=[SQUAD_UUID, SQUAD_UUID_2]),
        SimpleNamespace(connected_squads=[SQUAD_UUID_2]),
        SimpleNamespace(connected_squads=[]),
    ]
    db = SimpleNamespace(
        execute=lambda *args, **kwargs: None,
    )

    async def execute(*args: Any, **kwargs: Any) -> Any:
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: subscriptions))

    db.execute = execute

    updated = await _remove_retired_metered_squads(db, {SQUAD_UUID_2})

    assert updated == 2
    assert subscriptions[0].connected_squads == [SQUAD_UUID]
    assert subscriptions[1].connected_squads == []


@pytest.mark.asyncio
async def test_configuration_payload_exposes_all_selected_squads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = {
        'ULTIMA_METERED_TRAFFIC_ENABLED': True,
        'ULTIMA_METERED_SQUAD_UUID': f'{SQUAD_UUID},{SQUAD_UUID_2}',
        'ULTIMA_METERED_NODE_UUIDS': '',
        'ULTIMA_METERED_CHECK_INTERVAL_SECONDS': 60,
        'ULTIMA_METERED_WARNING_PERCENT': 80,
        'ULTIMA_METERED_SERVER_LABEL': 'Спецсерверы',
        'ULTIMA_METERED_EXHAUSTED_MESSAGE_RU': 'Лимит исчерпан',
    }

    monkeypatch.setattr(
        admin_settings.bot_configuration_service,
        'get_current_value',
        values.get,
    )

    async def fake_status(db: Any) -> dict[str, Any]:
        return {'enabled': True, 'squad_uuids': [SQUAD_UUID, SQUAD_UUID_2]}

    monkeypatch.setattr(admin_settings, '_metered_status_payload', fake_status)

    response = await _metered_configuration_payload(
        SimpleNamespace(),
        topology=(
            [
                SimpleNamespace(uuid=SQUAD_UUID, name='Metered 1', members_count=1, inbounds_count=0),
                SimpleNamespace(uuid=SQUAD_UUID_2, name='Metered 2', members_count=1, inbounds_count=0),
            ],
            [],
        ),
    )

    assert response['configuration']['squad_uuids'] == [SQUAD_UUID, SQUAD_UUID_2]
    assert response['configuration']['squad_uuid'] == SQUAD_UUID


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
    squads = [
        SimpleNamespace(uuid=SQUAD_UUID, name='Metered 1', members_count=10, inbounds=[]),
        SimpleNamespace(uuid=SQUAD_UUID_2, name='Metered 2', members_count=8, inbounds=[]),
    ]
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
        f'node:2:{METERED_NODE_UUID}',
        f'node:0:{UNLIMITED_NODE_UUID}',
    ]
    assert events[-2:] == ['commit', 'start']
    assert saved_values['ULTIMA_METERED_SQUAD_UUID'] == f'{SQUAD_UUID},{SQUAD_UUID_2}'
    assert saved_values['ULTIMA_METERED_NODE_UUIDS'] == METERED_NODE_UUID
    assert saved_values['ULTIMA_METERED_NODE_MULTIPLIERS'] == f'{{"{METERED_NODE_UUID}":2.0}}'
    assert saved_values['ULTIMA_METERED_TRAFFIC_ENABLED'] is True


@pytest.mark.asyncio
async def test_configuration_requires_metered_node_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    squads = [SimpleNamespace(uuid=SQUAD_UUID), SimpleNamespace(uuid=SQUAD_UUID_2)]
    nodes = [SimpleNamespace(uuid=METERED_NODE_UUID)]

    async def fake_load_topology() -> tuple[list[Any], list[Any]]:
        return squads, nodes

    monkeypatch.setattr(admin_settings, '_load_metered_topology', fake_load_topology)

    with pytest.raises(HTTPException) as exc_info:
        await admin_settings.update_metered_traffic_configuration(
            _payload(metered_node_uuids=[], metered_node_multipliers={}),
            admin=SimpleNamespace(telegram_id=42),
            db=FakeDb([]),
        )

    assert exc_info.value.status_code == 400
    assert 'хотя бы одну' in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_configuration_requires_at_least_one_squad_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    squads = [SimpleNamespace(uuid=SQUAD_UUID), SimpleNamespace(uuid=SQUAD_UUID_2)]
    nodes = [SimpleNamespace(uuid=METERED_NODE_UUID)]

    async def fake_load_topology() -> tuple[list[Any], list[Any]]:
        return squads, nodes

    monkeypatch.setattr(admin_settings, '_load_metered_topology', fake_load_topology)

    with pytest.raises(HTTPException) as exc_info:
        await admin_settings.update_metered_traffic_configuration(
            _payload(squad_uuids=[]),
            admin=SimpleNamespace(telegram_id=42),
            db=FakeDb([]),
        )

    assert exc_info.value.status_code == 400
    assert 'хотя бы один' in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_configuration_rejects_out_of_range_node_multiplier(monkeypatch: pytest.MonkeyPatch) -> None:
    squads = [SimpleNamespace(uuid=SQUAD_UUID), SimpleNamespace(uuid=SQUAD_UUID_2)]
    nodes = [SimpleNamespace(uuid=METERED_NODE_UUID)]

    async def fake_load_topology() -> tuple[list[Any], list[Any]]:
        return squads, nodes

    monkeypatch.setattr(admin_settings, '_load_metered_topology', fake_load_topology)

    with pytest.raises(HTTPException) as exc_info:
        await admin_settings.update_metered_traffic_configuration(
            _payload(metered_node_multipliers={METERED_NODE_UUID: 101}),
            admin=SimpleNamespace(telegram_id=42),
            db=FakeDb([]),
        )

    assert exc_info.value.status_code == 400
    assert '0.1 до 100' in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_configuration_restores_coefficients_and_monitor_after_partial_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    squads = [SimpleNamespace(uuid=SQUAD_UUID), SimpleNamespace(uuid=SQUAD_UUID_2)]
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
        f'node:2:{METERED_NODE_UUID}',
        f'node:0:{UNLIMITED_NODE_UUID}',
        'rollback',
        f'node:0:{METERED_NODE_UUID}',
        f'node:1:{UNLIMITED_NODE_UUID}',
        'start',
    ]
