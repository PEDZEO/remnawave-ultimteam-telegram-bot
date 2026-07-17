import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from app.config import settings
from app.external.remnawave_api import UserStatus
from app.services.metered_traffic_policy import BYTES_PER_GB
from app.services.metered_traffic_service import MeteredTrafficService


METERED_SQUAD_UUID = '11111111-1111-1111-1111-111111111111'
STANDARD_SQUAD_UUID = '22222222-2222-2222-2222-222222222222'


@pytest.fixture
def metered_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, 'ULTIMA_METERED_TRAFFIC_ENABLED', True)
    monkeypatch.setattr(settings, 'ULTIMA_METERED_SQUAD_UUID', METERED_SQUAD_UUID)
    monkeypatch.setattr(settings, 'ULTIMA_METERED_NODE_UUIDS', '33333333-3333-3333-3333-333333333333')
    monkeypatch.setattr(settings, 'ULTIMA_METERED_WARNING_PERCENT', 80)


def _subscription(**overrides: Any) -> SimpleNamespace:
    values = {
        'connected_squads': [STANDARD_SQUAD_UUID, METERED_SQUAD_UUID],
        'traffic_limit_gb': 100,
        'traffic_used_gb': 84.0,
        'metered_traffic_baseline_bytes': 0,
        'metered_traffic_last_counter_bytes': 84 * BYTES_PER_GB,
        'metered_traffic_initialized_at': datetime.now(UTC),
        'metered_traffic_last_checked_at': datetime.now(UTC),
        'metered_access_blocked': False,
        'metered_access_blocked_at': None,
        'metered_warning_percent': 80,
        'tariff': SimpleNamespace(special_servers_enabled=True),
        'user': SimpleNamespace(notification_settings={}),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _panel_user(**overrides: Any) -> SimpleNamespace:
    values = {
        'uuid': 'panel-user',
        'used_traffic_bytes': 85 * BYTES_PER_GB,
        'active_internal_squads': [
            {'uuid': STANDARD_SQUAD_UUID},
            {'uuid': METERED_SQUAD_UUID},
        ],
        'traffic_limit_bytes': 0,
        'status': UserStatus.ACTIVE,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_panel_users_are_loaded_lazily_page_by_page() -> None:
    users = [SimpleNamespace(uuid=f'user-{index}') for index in range(2250)]

    class FakeApi:
        def __init__(self) -> None:
            self.starts: list[int] = []

        async def get_all_users(
            self,
            *,
            start: int,
            size: int,
            enrich_happ_links: bool,
        ) -> dict[str, Any]:
            self.starts.append(start)
            return {
                'users': users[start : start + size],
                'total': len(users),
            }

    api = FakeApi()
    pages = MeteredTrafficService._iter_panel_user_pages(api)

    first = await anext(pages)
    assert len(first) == 1000
    assert api.starts == [0]

    second = await anext(pages)
    assert len(second) == 1000
    assert api.starts == [0, 1000]

    third = await anext(pages)
    assert len(third) == 250
    assert api.starts == [0, 1000, 2000]

    with pytest.raises(StopAsyncIteration):
        await anext(pages)


@pytest.mark.asyncio
async def test_page_processing_is_bounded_and_failures_are_isolated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = MeteredTrafficService()
    users = [SimpleNamespace(uuid=f'user-{index}') for index in range(40)]
    active_workers = 0
    max_active_workers = 0
    state_lock = asyncio.Lock()

    async def process_user(api: Any, panel_user: Any) -> dict[str, bool]:
        nonlocal active_workers, max_active_workers
        async with state_lock:
            active_workers += 1
            max_active_workers = max(max_active_workers, active_workers)
        try:
            await asyncio.sleep(0.002)
            if panel_user.uuid == 'user-17':
                raise RuntimeError('isolated failure')
            return {'initialized': False}
        finally:
            async with state_lock:
                active_workers -= 1

    monkeypatch.setattr(service, '_process_panel_user', process_user)

    page_result = await service._process_panel_users_concurrently(SimpleNamespace(), users)
    results = page_result.results

    assert len(results) == len(users)
    assert max_active_workers == 8
    assert sum(error is not None for _, _, error in results) == 1
    assert results[17][2] is not None
    assert page_result.circuit_open is False
    assert page_result.deferred == 0


@pytest.mark.asyncio
async def test_systemic_failure_opens_circuit_before_the_whole_page_is_queued(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = MeteredTrafficService()
    users = [SimpleNamespace(uuid=f'user-{index}') for index in range(1000)]

    async def process_user(api: Any, panel_user: Any) -> dict[str, bool]:
        raise TimeoutError(panel_user.uuid)

    monkeypatch.setattr(service, '_process_panel_user', process_user)

    page_result = await service._process_panel_users_concurrently(SimpleNamespace(), users)

    assert page_result.circuit_open is True
    assert len(page_result.results) == 8
    assert page_result.deferred == 992


@pytest.mark.parametrize(
    ('interval_seconds', 'elapsed_seconds', 'expected_delay'),
    [
        (60, 4.5, 55.5),
        (60, 60, 5.0),
        (60, 180, 5.0),
        (3, 10, 3.0),
    ],
)
def test_loop_delay_keeps_cadence_without_busy_looping(
    interval_seconds: int,
    elapsed_seconds: float,
    expected_delay: float,
) -> None:
    assert MeteredTrafficService._calculate_loop_delay(interval_seconds, elapsed_seconds) == expected_delay


def test_fast_path_updates_healthy_usage_without_repeating_warning(metered_mode: None) -> None:
    service = MeteredTrafficService()
    subscription = _subscription()
    panel_user = _panel_user()

    assert service._requires_individual_processing(subscription, panel_user) is False

    result = service._apply_fast_path(subscription, panel_user, now=datetime.now(UTC))

    assert result['warned'] is False
    assert subscription.traffic_used_gb == 85.0
    assert subscription.metered_warning_percent == 80


def test_fast_path_defers_new_warning_and_panel_reconciliation(metered_mode: None) -> None:
    service = MeteredTrafficService()

    assert (
        service._requires_individual_processing(
            _subscription(metered_warning_percent=0),
            _panel_user(),
        )
        is True
    )
    assert (
        service._requires_individual_processing(
            _subscription(),
            _panel_user(active_internal_squads=[{'uuid': STANDARD_SQUAD_UUID}]),
        )
        is True
    )


def test_fast_path_keeps_exhaustion_timestamp_stable(metered_mode: None) -> None:
    service = MeteredTrafficService()
    blocked_at = datetime.now(UTC)
    subscription = _subscription(
        connected_squads=[STANDARD_SQUAD_UUID],
        traffic_used_gb=100.0,
        metered_traffic_last_counter_bytes=100 * BYTES_PER_GB,
        metered_access_blocked=True,
        metered_access_blocked_at=blocked_at,
        metered_warning_percent=100,
    )
    panel_user = _panel_user(
        used_traffic_bytes=101 * BYTES_PER_GB,
        active_internal_squads=[{'uuid': STANDARD_SQUAD_UUID}],
    )

    assert service._requires_individual_processing(subscription, panel_user) is False
    service._apply_fast_path(subscription, panel_user, now=datetime.now(UTC))

    assert subscription.metered_access_blocked_at == blocked_at
    assert subscription.traffic_used_gb == 101.0
