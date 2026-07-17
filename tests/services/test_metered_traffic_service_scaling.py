import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from app.services.metered_traffic_service import MeteredTrafficService


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
