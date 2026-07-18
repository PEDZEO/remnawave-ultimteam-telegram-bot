from datetime import datetime
from types import SimpleNamespace

import pytest

from app.config import settings
from app.services.metered_traffic_policy import (
    block_metered_access,
    build_subscription_squads,
    calculate_metered_usage,
    get_customer_squad_uuids,
    get_metered_node_multipliers,
    get_metered_squad_uuids,
    panel_traffic_limit_bytes,
    preserve_metered_squad,
    reset_metered_cycle,
    restore_metered_access_if_available,
    tariff_allows_traffic_topup,
)
from app.services.metered_traffic_service import MeteredTrafficService


METERED_SQUAD_UUID = '11111111-1111-1111-1111-111111111111'
METERED_SQUAD_UUID_2 = '11111111-1111-1111-1111-222222222222'
STANDARD_SQUAD_UUID = '22222222-2222-2222-2222-222222222222'


@pytest.fixture(autouse=True)
def _enable_metered_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, 'ULTIMA_METERED_TRAFFIC_ENABLED', True)
    monkeypatch.setattr(
        settings,
        'ULTIMA_METERED_SQUAD_UUID',
        f'{METERED_SQUAD_UUID},{METERED_SQUAD_UUID_2}',
    )
    monkeypatch.setattr(settings, 'ULTIMA_METERED_NODE_UUIDS', '33333333-3333-3333-3333-333333333333')
    monkeypatch.setattr(settings, 'ULTIMA_METERED_NODE_MULTIPLIERS', '{}')


def _subscription(**overrides):
    values = {
        'connected_squads': [STANDARD_SQUAD_UUID, METERED_SQUAD_UUID, METERED_SQUAD_UUID_2],
        'traffic_limit_gb': 100,
        'traffic_used_gb': 0.0,
        'metered_traffic_baseline_bytes': 0,
        'metered_traffic_last_counter_bytes': 0,
        'metered_traffic_initialized_at': None,
        'metered_traffic_last_checked_at': None,
        'metered_access_blocked': False,
        'metered_access_blocked_at': None,
        'metered_warning_percent': 0,
        'tariff': SimpleNamespace(special_servers_enabled=True),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_legacy_metered_node_list_defaults_to_one_multiplier() -> None:
    assert get_metered_node_multipliers() == {
        '33333333-3333-3333-3333-333333333333': 1.0,
    }


def test_metered_squad_list_supports_multiple_and_legacy_single_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert get_metered_squad_uuids() == [METERED_SQUAD_UUID, METERED_SQUAD_UUID_2]

    monkeypatch.setattr(settings, 'ULTIMA_METERED_SQUAD_UUID', METERED_SQUAD_UUID)
    assert get_metered_squad_uuids() == [METERED_SQUAD_UUID]


def test_panel_limit_is_unlimited_only_in_metered_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    assert panel_traffic_limit_bytes(35) == 0

    monkeypatch.setattr(settings, 'ULTIMA_METERED_TRAFFIC_ENABLED', False)
    assert panel_traffic_limit_bytes(35) == 35 * 1024**3


def test_usage_is_measured_from_baseline_and_survives_counter_reset() -> None:
    used, baseline, reset = calculate_metered_usage(
        panel_counter_bytes=150,
        baseline_bytes=100,
        last_counter_bytes=140,
    )
    assert (used, baseline, reset) == (50, 100, False)

    used, baseline, reset = calculate_metered_usage(
        panel_counter_bytes=5,
        baseline_bytes=100,
        last_counter_bytes=150,
    )
    assert (used, baseline, reset) == (5, 0, True)


def test_exhaustion_removes_only_metered_squad_and_is_idempotent() -> None:
    subscription = _subscription()

    block_metered_access(subscription)
    first_blocked_at = subscription.metered_access_blocked_at
    block_metered_access(subscription)

    assert subscription.connected_squads == [STANDARD_SQUAD_UUID]
    assert subscription.metered_access_blocked is True
    assert isinstance(first_blocked_at, datetime)
    assert subscription.metered_access_blocked_at == first_blocked_at
    assert subscription.metered_warning_percent == 100


def test_healthy_reconciliation_keeps_warning_delivery_marker() -> None:
    subscription = _subscription(metered_warning_percent=80)

    assert restore_metered_access_if_available(subscription) is False
    assert subscription.metered_warning_percent == 80


def test_topup_restores_metered_squad_without_touching_standard_squad() -> None:
    subscription = _subscription(
        connected_squads=[STANDARD_SQUAD_UUID],
        traffic_limit_gb=110,
        traffic_used_gb=100.0,
        metered_access_blocked=True,
    )

    assert restore_metered_access_if_available(subscription) is True
    assert subscription.connected_squads == [
        STANDARD_SQUAD_UUID,
        METERED_SQUAD_UUID,
        METERED_SQUAD_UUID_2,
    ]
    assert subscription.metered_access_blocked is False
    assert subscription.metered_warning_percent == 0


def test_monitor_entitles_active_subscription_when_system_squad_is_missing() -> None:
    subscription = _subscription(connected_squads=[STANDARD_SQUAD_UUID])

    assert restore_metered_access_if_available(subscription) is True
    assert subscription.connected_squads == [
        STANDARD_SQUAD_UUID,
        METERED_SQUAD_UUID,
        METERED_SQUAD_UUID_2,
    ]


def test_tariff_without_special_servers_never_receives_metered_squad() -> None:
    subscription = _subscription(
        connected_squads=[STANDARD_SQUAD_UUID, METERED_SQUAD_UUID, METERED_SQUAD_UUID_2],
        tariff=SimpleNamespace(special_servers_enabled=False),
    )

    assert build_subscription_squads(subscription) == [STANDARD_SQUAD_UUID]
    assert restore_metered_access_if_available(subscription) is True
    assert subscription.connected_squads == [STANDARD_SQUAD_UUID]
    assert subscription.metered_access_blocked is False


def test_special_server_tariff_keeps_metered_squad_out_after_exhaustion() -> None:
    subscription = _subscription(
        connected_squads=[STANDARD_SQUAD_UUID],
        traffic_used_gb=100.0,
        metered_access_blocked=True,
    )

    assert build_subscription_squads(subscription) == [STANDARD_SQUAD_UUID]


def test_tariff_traffic_topup_requires_special_servers() -> None:
    tariff = SimpleNamespace(
        special_servers_enabled=False,
        can_topup_traffic=lambda: True,
    )

    assert tariff_allows_traffic_topup(tariff) is False

    tariff.special_servers_enabled = True
    assert tariff_allows_traffic_topup(tariff) is True


def test_system_squad_is_hidden_and_preserved_during_customer_selection() -> None:
    assert get_customer_squad_uuids([STANDARD_SQUAD_UUID, METERED_SQUAD_UUID, METERED_SQUAD_UUID_2]) == [
        STANDARD_SQUAD_UUID
    ]
    assert preserve_metered_squad(
        [STANDARD_SQUAD_UUID, METERED_SQUAD_UUID, METERED_SQUAD_UUID_2],
        [STANDARD_SQUAD_UUID],
    ) == [STANDARD_SQUAD_UUID, METERED_SQUAD_UUID, METERED_SQUAD_UUID_2]


def test_reset_cycle_uses_current_panel_counter_and_restores_access() -> None:
    subscription = _subscription(
        connected_squads=[STANDARD_SQUAD_UUID],
        traffic_used_gb=100.0,
        metered_access_blocked=True,
        metered_warning_percent=100,
    )

    reset_metered_cycle(subscription, panel_counter_bytes=987654321)

    assert subscription.metered_traffic_baseline_bytes == 987654321
    assert subscription.metered_traffic_last_counter_bytes == 987654321
    assert subscription.traffic_used_gb == 0.0
    assert subscription.connected_squads == [
        STANDARD_SQUAD_UUID,
        METERED_SQUAD_UUID,
        METERED_SQUAD_UUID_2,
    ]
    assert subscription.metered_access_blocked is False
    assert subscription.metered_warning_percent == 0


@pytest.mark.asyncio
async def test_topology_validation_accepts_configured_multiplier_for_metered_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        'ULTIMA_METERED_NODE_MULTIPLIERS',
        '{"33333333-3333-3333-3333-333333333333":2}',
    )

    class FakeApi:
        async def get_all_nodes(self):
            return [
                SimpleNamespace(
                    uuid='33333333-3333-3333-3333-333333333333',
                    name='Metered',
                    consumption_multiplier=2,
                ),
                SimpleNamespace(
                    uuid='44444444-4444-4444-4444-444444444444',
                    name='Unlimited',
                    consumption_multiplier=0,
                ),
            ]

    assert await MeteredTrafficService._validate_node_multipliers(FakeApi()) == []


@pytest.mark.asyncio
async def test_topology_validation_reconciles_unsafe_multipliers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        settings,
        'ULTIMA_METERED_NODE_MULTIPLIERS',
        '{"33333333-3333-3333-3333-333333333333":2}',
    )

    class FakeApi:
        def __init__(self) -> None:
            self.updates: list[tuple[list[str], float]] = []

        async def get_all_nodes(self):
            return [
                SimpleNamespace(
                    uuid='33333333-3333-3333-3333-333333333333',
                    name='Metered',
                    consumption_multiplier=1.3,
                ),
                SimpleNamespace(
                    uuid='44444444-4444-4444-4444-444444444444',
                    name='Unlimited',
                    consumption_multiplier=1,
                ),
            ]

        async def update_nodes_consumption_multiplier(self, uuids: list[str], multiplier: float) -> bool:
            self.updates.append((uuids, multiplier))
            return True

    api = FakeApi()

    errors = await MeteredTrafficService._validate_node_multipliers(api)

    assert errors == []
    assert api.updates == [
        (['33333333-3333-3333-3333-333333333333'], 2),
        (['44444444-4444-4444-4444-444444444444'], 0.0),
    ]


@pytest.mark.asyncio
async def test_topology_validation_reports_failed_automatic_reconciliation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, 'ULTIMA_METERED_NODE_UUIDS', '')
    monkeypatch.setattr(settings, 'ULTIMA_METERED_NODE_MULTIPLIERS', '{}')

    class FakeApi:
        async def get_all_nodes(self):
            return [
                SimpleNamespace(
                    uuid='55555555-5555-5555-5555-555555555555',
                    name='New node',
                    consumption_multiplier=1,
                ),
            ]

        async def update_nodes_consumption_multiplier(self, uuids: list[str], multiplier: float) -> bool:
            assert uuids == ['55555555-5555-5555-5555-555555555555']
            assert multiplier == 0.0
            return False

    errors = await MeteredTrafficService._validate_node_multipliers(FakeApi())

    assert errors == ['Не удалось установить коэффициент 0 для нод: New node']
