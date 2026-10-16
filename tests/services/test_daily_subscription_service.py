from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.services.daily_subscription_service as daily_service_module
from app.services.daily_subscription_service import DailySubscriptionService


class _ScalarResult:
    def __init__(self, *, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = list(rows or [])

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return self

    def all(self):
        return list(self._rows)


class _FakeSession:
    def __init__(self, subscription, purchases):
        self.subscription = subscription
        self.purchases = list(purchases)
        self.execute_calls = 0
        self.deleted = []
        self.commit = AsyncMock()
        self.flush = AsyncMock()
        self.rollback = AsyncMock()

    async def execute(self, _query):
        self.execute_calls += 1
        if self.execute_calls == 1:
            return _ScalarResult(scalar=self.subscription)
        return _ScalarResult(rows=self.purchases)

    async def delete(self, item):
        self.deleted.append(item)


def test_service_stays_enabled_for_traffic_expiry_when_daily_charges_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        daily_service_module,
        'settings',
        SimpleNamespace(
            DAILY_SUBSCRIPTIONS_ENABLED=False,
            TRAFFIC_TOPUP_EXPIRY_ENABLED=True,
            DAILY_SUBSCRIPTIONS_CHECK_INTERVAL_MINUTES=30,
            TRAFFIC_TOPUP_EXPIRY_CHECK_INTERVAL_SECONDS=60,
        ),
    )

    service = DailySubscriptionService()

    assert service.is_enabled() is True
    assert service.is_daily_charges_enabled() is False
    assert service.is_traffic_resets_enabled() is True


@pytest.mark.asyncio
async def test_reset_subscription_traffic_recalculates_from_purchase_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeSubscriptionService:
        async def update_remnawave_user(self, *_args, **_kwargs):
            return None

    import app.services.subscription_service as subscription_service_module

    monkeypatch.setattr(subscription_service_module, 'SubscriptionService', _FakeSubscriptionService)

    subscription = SimpleNamespace(
        id=10,
        user_id=None,
        tariff_id=None,
        traffic_limit_gb=110,
        purchased_traffic_gb=20,
        traffic_reset_at=datetime.now(UTC),
        updated_at=None,
    )
    expired_purchase = SimpleNamespace(traffic_gb=10, expires_at=datetime.now(UTC) - timedelta(days=1))
    db = _FakeSession(subscription, purchases=[expired_purchase])

    service = DailySubscriptionService()
    await service._reset_subscription_traffic(db, subscription.id)

    assert db.deleted == [expired_purchase]
    assert subscription.traffic_limit_gb == 100
    assert subscription.purchased_traffic_gb == 0
    assert subscription.traffic_reset_at is None
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_reset_subscription_traffic_keeps_remaining_active_purchases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeSubscriptionService:
        async def update_remnawave_user(self, *_args, **_kwargs):
            return None

    import app.services.subscription_service as subscription_service_module

    monkeypatch.setattr(subscription_service_module, 'SubscriptionService', _FakeSubscriptionService)

    next_expiry = datetime.now(UTC) + timedelta(days=7)
    subscription = SimpleNamespace(
        id=11,
        user_id=None,
        tariff_id=None,
        traffic_limit_gb=120,
        purchased_traffic_gb=20,
        traffic_reset_at=datetime.now(UTC),
        updated_at=None,
    )
    expired_purchase = SimpleNamespace(traffic_gb=10, expires_at=datetime.now(UTC) - timedelta(days=1))
    remaining_purchase = SimpleNamespace(traffic_gb=10, expires_at=next_expiry)
    db = _FakeSession(subscription, purchases=[expired_purchase, remaining_purchase])

    service = DailySubscriptionService()
    await service._reset_subscription_traffic(db, subscription.id)

    assert subscription.traffic_limit_gb == 110
    assert subscription.purchased_traffic_gb == 10
    assert subscription.traffic_reset_at == next_expiry


@pytest.mark.asyncio
async def test_reset_subscription_traffic_retries_when_remnawave_sync_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeSubscriptionService:
        async def update_remnawave_user(self, *_args, **_kwargs):
            return None

    import app.services.subscription_service as subscription_service_module

    monkeypatch.setattr(subscription_service_module, 'SubscriptionService', _FakeSubscriptionService)
    monkeypatch.setattr(
        daily_service_module,
        'get_user_by_id',
        AsyncMock(return_value=SimpleNamespace(remnawave_uuid='remna-user-id')),
    )

    subscription = SimpleNamespace(
        id=12,
        user_id=5,
        tariff_id=None,
        traffic_limit_gb=110,
        purchased_traffic_gb=10,
        traffic_reset_at=datetime.now(UTC),
        updated_at=None,
    )
    expired_purchase = SimpleNamespace(traffic_gb=10, expires_at=datetime.now(UTC) - timedelta(days=1))
    db = _FakeSession(subscription, purchases=[expired_purchase])

    service = DailySubscriptionService()
    with pytest.raises(RuntimeError, match='RemnaWave rejected'):
        await service._reset_subscription_traffic(db, subscription.id)

    assert db.deleted == [expired_purchase]
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_expiry_ignores_purchase_rows_removed_by_a_concurrent_tariff_change():
    subscription = SimpleNamespace(id=13, traffic_limit_gb=35, purchased_traffic_gb=0)
    db = _FakeSession(subscription, purchases=[])

    assert await DailySubscriptionService()._reset_subscription_traffic(db, subscription.id) == 0
    assert subscription.traffic_limit_gb == 35
    assert db.deleted == []
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_expiry_preserves_unlimited_quota():
    subscription = SimpleNamespace(
        id=14,
        user_id=None,
        tariff_id=None,
        traffic_limit_gb=0,
        purchased_traffic_gb=20,
        traffic_reset_at=None,
    )
    expired = SimpleNamespace(traffic_gb=10, expires_at=datetime.now(UTC) - timedelta(days=1))
    active = SimpleNamespace(traffic_gb=10, expires_at=datetime.now(UTC) + timedelta(days=1))
    db = _FakeSession(subscription, purchases=[expired, active])

    await DailySubscriptionService()._reset_subscription_traffic(db, subscription.id)

    assert subscription.traffic_limit_gb == 0
    assert subscription.purchased_traffic_gb == 10


@pytest.mark.asyncio
async def test_expiry_caps_metered_usage_so_new_topup_has_no_old_debt(monkeypatch):
    from app.config import settings
    from app.services.metered_traffic_policy import BYTES_PER_GB, restore_metered_access_if_available

    monkeypatch.setattr(settings, 'ULTIMA_METERED_TRAFFIC_ENABLED', True)
    monkeypatch.setattr(settings, 'ULTIMA_METERED_SQUAD_UUID', 'special')
    monkeypatch.setattr(settings, 'ULTIMA_METERED_NODE_UUIDS', 'node')
    initialized_at = datetime.now(UTC) - timedelta(days=40)
    subscription = SimpleNamespace(
        id=15,
        user_id=None,
        tariff_id=None,
        tariff=SimpleNamespace(special_servers_enabled=True),
        traffic_limit_gb=145,
        purchased_traffic_gb=20,
        device_bonus_traffic_gb=25,
        traffic_used_gb=140,
        metered_traffic_baseline_bytes=0,
        metered_traffic_initialized_at=initialized_at,
        metered_access_blocked=False,
        connected_squads=['standard', 'special'],
    )
    expired = SimpleNamespace(traffic_gb=20, expires_at=datetime.now(UTC) - timedelta(days=1))
    db = _FakeSession(subscription, purchases=[expired])

    await DailySubscriptionService()._reset_subscription_traffic(db, subscription.id)

    assert subscription.traffic_limit_gb == 125
    assert subscription.device_bonus_traffic_gb == 25
    assert subscription.traffic_used_gb == 125
    assert subscription.metered_traffic_baseline_bytes == 15 * BYTES_PER_GB
    assert subscription.metered_traffic_initialized_at == initialized_at
    assert subscription.connected_squads == ['standard']
    subscription.traffic_limit_gb += 10
    assert restore_metered_access_if_available(subscription) is True
    assert subscription.traffic_limit_gb - subscription.traffic_used_gb == 10
