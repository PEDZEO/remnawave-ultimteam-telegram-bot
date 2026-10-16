from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.cabinet.routes.subscription_helpers as response_module
import app.services.metered_traffic_policy as policy_module
import app.services.metered_traffic_service as monitor_module
import app.services.traffic_purchase_service as purchase_module
from app.config import settings
from app.database.crud.subscription import add_subscription_traffic
from app.database.models import Subscription, Tariff
from app.external.remnawave_api import TrafficLimitStrategy, UserStatus
from app.services.metered_traffic_policy import (
    BYTES_PER_GB,
    cap_metered_usage,
    get_metered_traffic_period,
    metered_cycle_is_due,
    rebase_metered_counter,
    refresh_metered_usage,
    reset_metered_cycle,
    restore_metered_access_if_available,
)
from app.services.metered_traffic_service import MeteredTrafficService
from app.services.subscription_service import get_traffic_reset_strategy


NOW = datetime(2026, 10, 16, 9, 30, tzinfo=UTC)
STANDARD = 'standard-squad'
SPECIAL = 'special-squad'


@pytest.fixture(autouse=True)
def metered_mode(monkeypatch):
    monkeypatch.setattr(settings, 'ULTIMA_METERED_TRAFFIC_ENABLED', True)
    monkeypatch.setattr(settings, 'ULTIMA_METERED_SQUAD_UUID', SPECIAL)
    monkeypatch.setattr(settings, 'ULTIMA_METERED_NODE_UUIDS', 'special-node')

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW.astimezone(tz or UTC)

    monkeypatch.setattr(purchase_module, 'datetime', _FrozenDatetime)
    monkeypatch.setattr(policy_module, 'datetime', _FrozenDatetime)


def _subscription(**overrides):
    values = dict(
        id=1,
        user_id=None,
        tariff_id=None,
        status='active',
        actual_status='active',
        start_date=datetime(2026, 7, 16, 9, 30, tzinfo=UTC),
        end_date=NOW + timedelta(days=60),
        traffic_limit_gb=100,
        traffic_used_gb=100.0,
        purchased_traffic_gb=0,
        connected_squads=[STANDARD],
        metered_access_blocked=True,
        metered_access_blocked_at=NOW - timedelta(days=40),
        metered_warning_percent=100,
        metered_traffic_initialized_at=datetime(2026, 7, 16, 9, 30, tzinfo=UTC),
        metered_traffic_baseline_bytes=10 * BYTES_PER_GB,
        metered_traffic_last_counter_bytes=110 * BYTES_PER_GB,
        metered_traffic_last_checked_at=NOW - timedelta(minutes=1),
        tariff=SimpleNamespace(special_servers_enabled=True),
        user=SimpleNamespace(notification_settings={}, remnawave_uuid='panel-user'),
    )
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    ('anchor', 'now', 'start', 'end'),
    [
        ('2026-01-31T09:30', '2026-02-28T09:29', '2026-01-31T09:30', '2026-02-28T09:30'),
        ('2026-01-31T09:30', '2026-02-28T09:30', '2026-02-28T09:30', '2026-03-31T09:30'),
        ('2024-01-31T09:30', '2024-02-29T09:30', '2024-02-29T09:30', '2024-03-31T09:30'),
        ('2026-07-31T09:30', '2026-10-16T09:30', '2026-09-30T09:30', '2026-10-31T09:30'),
        ('2025-12-31T09:30', '2026-01-31T09:30', '2026-01-31T09:30', '2026-02-28T09:30'),
        # January 30 UTC is January 31 in Moscow; anniversaries use Moscow dates.
        ('2026-01-30T21:30', '2026-02-27T21:30', '2026-02-27T21:30', '2026-03-30T21:30'),
    ],
)
def test_monthly_anniversaries_keep_original_day_and_connection_time(anchor, now, start, end):
    def utc(value):
        return datetime.fromisoformat(value).replace(tzinfo=UTC)

    subscription = _subscription(start_date=utc(anchor))
    assert get_metered_traffic_period(subscription, now=utc(now)) == (utc(start), utc(end))


def test_manual_reset_and_renewal_do_not_move_the_next_anniversary():
    subscription = _subscription(metered_traffic_initialized_at=NOW - timedelta(days=5))
    subscription.end_date += timedelta(days=90)

    assert metered_cycle_is_due(subscription, now=NOW - timedelta(seconds=1)) is False
    assert metered_cycle_is_due(subscription, now=NOW) is True
    reset_metered_cycle(subscription, panel_counter_bytes=400 * BYTES_PER_GB)
    assert get_metered_traffic_period(subscription, now=NOW)[1] == datetime(2026, 11, 16, 9, 30, tzinfo=UTC)


def test_multiple_missed_cycles_reset_once_and_keep_active_topups_and_device_bonus():
    subscription = _subscription(traffic_limit_gb=145, purchased_traffic_gb=20, device_bonus_traffic_gb=25)
    used, initialized, renewed = refresh_metered_usage(subscription, panel_counter_bytes=400 * BYTES_PER_GB, now=NOW)
    assert (used, initialized, renewed) == (0, False, True)
    assert subscription.traffic_limit_gb == 145
    assert subscription.purchased_traffic_gb == 20
    assert subscription.device_bonus_traffic_gb == 25
    assert subscription.metered_warning_percent == 0
    assert restore_metered_access_if_available(subscription) is True
    assert subscription.connected_squads == [STANDARD, SPECIAL]

    used, initialized, renewed = refresh_metered_usage(
        subscription, panel_counter_bytes=403 * BYTES_PER_GB, now=NOW + timedelta(minutes=1)
    )
    assert (used, initialized, renewed) == (3 * BYTES_PER_GB, False, False)


def test_first_sample_grants_fresh_baseline_and_nullable_anchor_uses_creation_date():
    subscription = _subscription(
        start_date=None, created_at=NOW - timedelta(days=90), metered_traffic_initialized_at=None
    )
    assert refresh_metered_usage(subscription, panel_counter_bytes=999 * BYTES_PER_GB, now=NOW) == (0, True, False)
    assert subscription.traffic_used_gb == 0
    period_start, next_reset = get_metered_traffic_period(subscription, now=NOW)
    assert period_start <= NOW < next_reset


def test_panel_counter_restart_preserves_current_month_usage_and_warning():
    subscription = _subscription(
        metered_access_blocked=False,
        metered_traffic_initialized_at=NOW,
        metered_traffic_baseline_bytes=90 * BYTES_PER_GB,
        metered_traffic_last_counter_bytes=110 * BYTES_PER_GB,
        traffic_used_gb=20,
        metered_warning_percent=75,
    )
    used, _, renewed = refresh_metered_usage(subscription, panel_counter_bytes=5 * BYTES_PER_GB, now=NOW)
    assert used == 25 * BYTES_PER_GB
    assert renewed is False
    assert subscription.metered_traffic_baseline_bytes == -20 * BYTES_PER_GB
    assert subscription.metered_warning_percent == 75
    used, _, _ = refresh_metered_usage(
        subscription, panel_counter_bytes=8 * BYTES_PER_GB, now=NOW + timedelta(minutes=1)
    )
    assert used == 28 * BYTES_PER_GB


def test_panel_reset_timestamp_detects_restart_even_after_counter_passes_previous_value():
    subscription = _subscription(
        metered_access_blocked=False,
        metered_traffic_initialized_at=NOW,
        metered_traffic_baseline_bytes=0,
        metered_traffic_last_counter_bytes=10 * BYTES_PER_GB,
    )
    used, _, _ = refresh_metered_usage(
        subscription,
        panel_counter_bytes=50 * BYTES_PER_GB,
        panel_reset_at=NOW - timedelta(seconds=30),
        now=NOW,
    )
    assert used == 60 * BYTES_PER_GB


def test_blocked_usage_cannot_grow_beyond_quota_or_consume_a_new_topup():
    subscription = _subscription(metered_traffic_initialized_at=NOW)
    refresh_metered_usage(subscription, panel_counter_bytes=400 * BYTES_PER_GB, now=NOW)
    assert subscription.traffic_used_gb == 100
    assert subscription.metered_traffic_baseline_bytes == 300 * BYTES_PER_GB

    subscription.traffic_limit_gb += 10
    assert restore_metered_access_if_available(subscription) is True
    refresh_metered_usage(subscription, panel_counter_bytes=402 * BYTES_PER_GB, now=NOW + timedelta(minutes=1))
    assert subscription.traffic_used_gb == 102
    assert subscription.traffic_limit_gb - subscription.traffic_used_gb == 8


def test_expiry_cap_does_not_hide_an_overdue_monthly_reset():
    subscription = _subscription(traffic_used_gb=350, metered_traffic_last_counter_bytes=360 * BYTES_PER_GB)
    initialized_at = subscription.metered_traffic_initialized_at
    assert cap_metered_usage(subscription) is True
    assert subscription.traffic_used_gb == 100
    assert subscription.metered_traffic_initialized_at == initialized_at
    assert metered_cycle_is_due(subscription, now=NOW) is True


@pytest.mark.asyncio
async def test_purchase_forgives_existing_overshoot_before_adding_new_quota():
    subscription = Subscription(
        id=1,
        user_id=1,
        traffic_limit_gb=100,
        traffic_used_gb=350,
        purchased_traffic_gb=0,
        metered_traffic_baseline_bytes=0,
    )
    result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=list))
    db = SimpleNamespace(
        add=lambda _purchase: None,
        execute=AsyncMock(return_value=result),
        flush=AsyncMock(),
        refresh=AsyncMock(),
    )

    await add_subscription_traffic(db, subscription, 10, commit=False)

    assert subscription.traffic_used_gb == 100
    assert subscription.traffic_limit_gb == 110
    assert subscription.purchased_traffic_gb == 10
    assert subscription.metered_traffic_baseline_bytes == 250 * BYTES_PER_GB


class _FakeSession:
    def __init__(self, subscription):
        self.subscription = subscription
        self.commit = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def execute(self, _query):
        return SimpleNamespace(
            scalar_one_or_none=lambda: self.subscription,
            scalars=lambda: SimpleNamespace(all=lambda: [self.subscription]),
        )

    async def scalars(self, _query):
        return SimpleNamespace(all=lambda: ['panel-user'])


def _monitor_context(monkeypatch, subscription):
    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW.astimezone(tz or UTC)

    monkeypatch.setattr(monitor_module, 'datetime', _FrozenDatetime)
    monkeypatch.setattr(MeteredTrafficService, '_notify_user', AsyncMock())
    db = _FakeSession(subscription)
    monkeypatch.setattr(monitor_module, 'AsyncSessionLocal', lambda: db)
    api = SimpleNamespace(
        update_user=AsyncMock(
            return_value=SimpleNamespace(used_traffic_bytes=400 * BYTES_PER_GB, last_traffic_reset_at=None)
        ),
        enable_user=AsyncMock(),
    )
    panel = SimpleNamespace(
        uuid='panel-user',
        used_traffic_bytes=400 * BYTES_PER_GB,
        active_internal_squads=[{'uuid': STANDARD}],
        traffic_limit_bytes=0,
        traffic_limit_strategy=TrafficLimitStrategy.MONTH,
        status=UserStatus.ACTIVE,
    )
    return db, api, panel


@pytest.mark.asyncio
async def test_monitor_renews_exhausted_subscription_and_restores_only_its_special_squad(monkeypatch):
    subscription = _subscription()
    db, api, panel = _monitor_context(monkeypatch, subscription)
    monitor = MeteredTrafficService()
    assert monitor._requires_individual_processing(subscription, panel, now=NOW) is True

    result = await monitor._process_panel_user(api, panel)

    assert result['renewed'] is True
    assert result['restored'] is True
    assert subscription.traffic_used_gb == 0
    assert subscription.metered_access_blocked is False
    api.update_user.assert_awaited_once_with(
        uuid='panel-user',
        traffic_limit_bytes=0,
        traffic_limit_strategy=TrafficLimitStrategy.NO_RESET,
        active_internal_squads=[STANDARD, SPECIAL],
    )
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_topup_restoration_ignores_bytes_reported_while_the_squad_was_blocked(monkeypatch):
    subscription = _subscription(metered_traffic_initialized_at=NOW, traffic_limit_gb=110)
    db, api, panel = _monitor_context(monkeypatch, subscription)
    panel.traffic_limit_strategy = TrafficLimitStrategy.NO_RESET
    api.update_user.return_value.used_traffic_bytes = 405 * BYTES_PER_GB
    monitor = MeteredTrafficService()
    assert monitor._requires_individual_processing(subscription, panel, now=NOW) is True

    result = await monitor._process_panel_user(api, panel)

    assert result['restored'] is True
    assert subscription.traffic_used_gb == 100
    assert subscription.metered_traffic_baseline_bytes == 305 * BYTES_PER_GB
    assert subscription.metered_traffic_last_counter_bytes == 405 * BYTES_PER_GB
    refresh_metered_usage(subscription, panel_counter_bytes=408 * BYTES_PER_GB, now=NOW + timedelta(minutes=1))
    assert subscription.traffic_limit_gb - subscription.traffic_used_gb == 7
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_monitor_does_not_commit_rollover_when_panel_rejects_restoration(monkeypatch):
    db, api, panel = _monitor_context(monkeypatch, _subscription())
    api.update_user.side_effect = RuntimeError('panel unavailable')
    with pytest.raises(RuntimeError, match='panel unavailable'):
        await MeteredTrafficService()._process_panel_user(api, panel)
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_monitor_skips_sample_taken_before_a_manual_reset(monkeypatch):
    subscription = _subscription(metered_traffic_last_checked_at=NOW)
    db, api, panel = _monitor_context(monkeypatch, subscription)
    initialized_at = subscription.metered_traffic_initialized_at
    assert await MeteredTrafficService()._process_panel_user(api, panel, sampled_at=NOW - timedelta(seconds=1)) is None
    assert subscription.metered_traffic_initialized_at == initialized_at
    api.update_user.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('active', [False, True])
async def test_monitor_never_grants_special_access_without_both_active_subscription_and_entitlement(
    monkeypatch, active
):
    subscription = _subscription(
        end_date=NOW + timedelta(days=1) if active else NOW - timedelta(seconds=1),
        tariff=SimpleNamespace(special_servers_enabled=False),
    )
    db, api, panel = _monitor_context(monkeypatch, subscription)
    await MeteredTrafficService()._process_panel_user(api, panel)
    assert SPECIAL not in subscription.connected_squads
    if not active:
        api.update_user.assert_not_awaited()
        db.commit.assert_not_awaited()


def test_only_metered_mode_disables_the_panels_independent_calendar_reset(monkeypatch):
    tariff = SimpleNamespace(traffic_reset_mode='MONTH', name='Monthly')
    assert get_traffic_reset_strategy(tariff) == TrafficLimitStrategy.NO_RESET
    monkeypatch.setattr(settings, 'ULTIMA_METERED_TRAFFIC_ENABLED', False)
    assert get_traffic_reset_strategy(tariff) == TrafficLimitStrategy.MONTH


def test_cabinet_exposes_anniversary_and_monthly_base_including_device_bonus(monkeypatch):
    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW.astimezone(tz or UTC)

    monkeypatch.setattr(response_module, 'datetime', _FrozenDatetime)
    tariff = Tariff(id=7, name='Special', special_servers_enabled=True, traffic_reset_mode='NO_RESET', is_daily=False)
    subscription = Subscription(
        id=1,
        user_id=1,
        status='active',
        is_trial=False,
        start_date=NOW - timedelta(days=92),
        end_date=datetime(2099, 1, 1, tzinfo=UTC),
        traffic_limit_gb=135,
        traffic_used_gb=40,
        purchased_traffic_gb=10,
        tariff_id=7,
        tariff=tariff,
    )
    response = response_module.subscription_to_response(subscription)
    assert response.traffic_reset_mode == 'MONTH'
    assert response.metered_traffic_reset_timezone == 'Europe/Moscow'
    assert response.metered_traffic_reset_at == get_metered_traffic_period(subscription, now=NOW)[1]
    assert response.metered_traffic_base_limit_gb == 125
    assert response.purchased_traffic_gb == 10


class _TopupSession:
    def __init__(self, purchases=()):
        self.purchases = list(purchases)
        self.refresh = AsyncMock()
        self.flush = AsyncMock()
        self.get = AsyncMock(return_value=SimpleNamespace(remnawave_uuid='panel-user'))
        self.commit = AsyncMock()

    async def execute(self, _query):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: list(self.purchases)))

    def add(self, purchase):
        self.purchases.append(purchase)

    async def delete(self, purchase):
        self.purchases.remove(purchase)


def _mock_purchase_panel(monkeypatch, used_gb):
    from app.services.remnawave_service import RemnaWaveService

    api = SimpleNamespace(
        get_user_by_uuid=AsyncMock(
            return_value=SimpleNamespace(used_traffic_bytes=used_gb * BYTES_PER_GB, last_traffic_reset_at=None)
        )
    )

    @asynccontextmanager
    async def client(_self):
        yield api

    monkeypatch.setattr(RemnaWaveService, 'get_api_client', client)
    return api


@pytest.mark.asyncio
async def test_unobserved_overshoot_is_settled_against_old_quota_before_purchase(monkeypatch):
    _mock_purchase_panel(monkeypatch, used_gb=130)
    subscription = Subscription(
        id=1,
        user_id=1,
        start_date=NOW - timedelta(days=10),
        tariff=Tariff(special_servers_enabled=True),
        traffic_limit_gb=100,
        traffic_used_gb=95,
        purchased_traffic_gb=0,
        metered_traffic_initialized_at=NOW,
        metered_traffic_baseline_bytes=0,
        metered_traffic_last_counter_bytes=95 * BYTES_PER_GB,
        metered_traffic_last_checked_at=NOW - timedelta(seconds=60),
        metered_access_blocked=False,
        connected_squads=[STANDARD, SPECIAL],
    )
    await add_subscription_traffic(_TopupSession(), subscription, 10, commit=False)

    assert subscription.traffic_used_gb == 100
    assert subscription.traffic_limit_gb == 110
    assert subscription.metered_access_blocked is True
    assert subscription.metered_traffic_baseline_bytes == 30 * BYTES_PER_GB
    assert subscription.traffic_limit_gb - subscription.traffic_used_gb == 10


@pytest.mark.asyncio
@pytest.mark.parametrize('expiry_first', [False, True])
async def test_topup_result_does_not_depend_on_expiry_worker_order(monkeypatch, expiry_first):
    _mock_purchase_panel(monkeypatch, used_gb=140)
    expired = SimpleNamespace(traffic_gb=50, expires_at=NOW - timedelta(days=1))
    subscription = Subscription(
        id=1,
        user_id=1,
        start_date=NOW - timedelta(days=10),
        tariff=Tariff(special_servers_enabled=True),
        traffic_limit_gb=150,
        traffic_used_gb=140,
        purchased_traffic_gb=50,
        metered_traffic_initialized_at=NOW,
        metered_traffic_baseline_bytes=0,
        metered_traffic_last_counter_bytes=140 * BYTES_PER_GB,
        metered_traffic_last_checked_at=NOW - timedelta(seconds=60),
        metered_access_blocked=False,
        connected_squads=[STANDARD, SPECIAL],
    )
    db = _TopupSession([expired])
    if expiry_first:
        await purchase_module.remove_expired_traffic_purchases(db, subscription, now=NOW)

    await add_subscription_traffic(db, subscription, 10, commit=False)

    assert subscription.traffic_used_gb == 100
    assert subscription.traffic_limit_gb == 110
    assert subscription.purchased_traffic_gb == 10
    assert len(db.purchases) == 1
    assert subscription.traffic_limit_gb - subscription.traffic_used_gb == 10


@pytest.mark.asyncio
@pytest.mark.parametrize('fast_path', [False, True])
async def test_counter_epoch_is_tracked_from_observation_not_processing_time(monkeypatch, fast_path):
    subscription = _subscription(
        metered_traffic_initialized_at=NOW,
        metered_access_blocked=False,
        connected_squads=[STANDARD, SPECIAL],
        metered_traffic_baseline_bytes=0,
        metered_traffic_last_counter_bytes=20 * BYTES_PER_GB,
        traffic_used_gb=20,
        metered_warning_percent=0,
    )
    _, api, panel = _monitor_context(monkeypatch, subscription)
    panel.active_internal_squads = [{'uuid': STANDARD}, {'uuid': SPECIAL}]
    panel.traffic_limit_strategy = TrafficLimitStrategy.NO_RESET
    panel.used_traffic_bytes = 20 * BYTES_PER_GB
    panel.last_traffic_reset_at = None
    monitor = MeteredTrafficService()

    async def sample(observed_at):
        if fast_path:
            monitor._apply_fast_path(subscription, panel, now=NOW, sampled_at=observed_at)
        else:
            await monitor._process_panel_user(api, panel, sampled_at=observed_at)

    await sample(NOW - timedelta(seconds=3))
    panel.used_traffic_bytes = 30 * BYTES_PER_GB
    panel.last_traffic_reset_at = NOW - timedelta(seconds=2)
    await sample(NOW - timedelta(seconds=1))
    assert subscription.traffic_used_gb == 50
    panel.used_traffic_bytes = 35 * BYTES_PER_GB
    await sample(NOW)
    assert subscription.traffic_used_gb == 55


@pytest.mark.asyncio
@pytest.mark.parametrize('fast_path', [False, True])
async def test_restoration_rejects_an_overlapping_get_with_older_counter(monkeypatch, fast_path):
    subscription = _subscription(
        metered_traffic_initialized_at=NOW,
        metered_access_blocked=False,
        traffic_limit_gb=110,
        connected_squads=[STANDARD, SPECIAL],
    )
    _, api, panel = _monitor_context(monkeypatch, subscription)
    rebase_metered_counter(subscription, panel_counter_bytes=405 * BYTES_PER_GB, sampled_at=NOW - timedelta(seconds=3))
    panel.used_traffic_bytes = 400 * BYTES_PER_GB
    observed_at = NOW - timedelta(seconds=2)
    monitor = MeteredTrafficService()
    if fast_path:
        result = await monitor._process_panel_users_fast_path([panel], sampled_at=observed_at)
        assert result.deferred == 1
        assert result.results == []
    else:
        assert await monitor._process_panel_user(api, panel, sampled_at=observed_at) is None
    assert subscription.traffic_used_gb == 100
    assert subscription.traffic_limit_gb - subscription.traffic_used_gb == 10
    api.update_user.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('user', [None, SimpleNamespace(remnawave_uuid=None)])
async def test_missing_panel_identity_cannot_grant_unsettled_quota(user):
    subscription = Subscription(
        id=1,
        user_id=1,
        tariff=Tariff(special_servers_enabled=True),
        traffic_limit_gb=100,
        purchased_traffic_gb=0,
        traffic_used_gb=95,
    )
    db = _TopupSession()
    db.get.return_value = user
    with pytest.raises(RuntimeError, match='panel identity'):
        await add_subscription_traffic(db, subscription, 10, commit=False)
    assert subscription.traffic_limit_gb == 100
    assert subscription.traffic_used_gb == 95
    assert db.purchases == []
    db.commit.assert_not_awaited()
