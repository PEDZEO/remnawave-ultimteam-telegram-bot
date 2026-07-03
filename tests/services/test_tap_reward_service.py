from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.services.tap_reward_service as tap_reward_module


pytestmark = pytest.mark.asyncio


def _db():
    return SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock(), flush=AsyncMock())


def _progress(**overrides):
    now = datetime.now(UTC)
    data = {
        'user_id': 1,
        'total_taps': 0,
        'streak_taps': 0,
        'reward_count': 0,
        'streak_reward_count': 0,
        'daily_reward_count': 0,
        'daily_reward_date': now.date(),
        'last_tap_at': None,
        'last_reward_at': None,
        'updated_at': None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _daily_stats(**overrides):
    data = {
        'user_id': 1,
        'stat_date': datetime.now(UTC).date(),
        'tap_count': 0,
        'reward_count': 0,
        'balance_reward_kopeks': 0,
        'subscription_reward_days': 0,
        'last_tap_at': None,
        'last_reward_at': None,
        'updated_at': None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _patch_daily_stats(monkeypatch, service, daily_stats=None):
    daily_stats = daily_stats or _daily_stats()
    notification_mock = AsyncMock()
    monkeypatch.setattr(service, '_get_or_create_daily_stats', AsyncMock(return_value=daily_stats))
    monkeypatch.setattr(service, '_send_reward_admin_notification', notification_mock)
    return daily_stats, notification_mock


async def test_tap_reward_grants_balance_at_threshold(monkeypatch):
    service = tap_reward_module.TapRewardService()
    progress = _progress()
    user = SimpleNamespace(id=1, balance_kopeks=0)
    db = _db()

    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_ENABLED', True)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_THRESHOLD', 3)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_REWARD_TYPE', 'balance')
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_BALANCE_KOPEKS', 5000)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_DAILY_REWARD_LIMIT', 1)
    monkeypatch.setattr(service, '_get_or_create_progress', AsyncMock(return_value=progress))
    daily_stats, notification_mock = _patch_daily_stats(monkeypatch, service)

    async def add_balance(_db, target_user, amount, **_kwargs):
        target_user.balance_kopeks += amount
        return True

    add_balance_mock = AsyncMock(side_effect=add_balance)
    monkeypatch.setattr(tap_reward_module, 'add_user_balance', add_balance_mock)

    result = await service.record_taps(db, user, 3)

    assert result.reward_granted is True
    assert result.reward_type == 'balance'
    assert result.reward_value == 5000
    assert result.balance_kopeks == 5000
    assert progress.total_taps == 3
    assert progress.reward_count == 1
    assert progress.daily_reward_count == 1
    assert daily_stats.tap_count == 3
    assert daily_stats.reward_count == 1
    assert daily_stats.balance_reward_kopeks == 5000
    notification_mock.assert_awaited_once()
    add_balance_mock.assert_awaited_once()


async def test_tap_reward_daily_limit_keeps_unclaimed_progress(monkeypatch):
    service = tap_reward_module.TapRewardService()
    progress = _progress(total_taps=3, streak_taps=3, reward_count=1, streak_reward_count=1, daily_reward_count=1)
    user = SimpleNamespace(id=1, balance_kopeks=0)
    db = _db()

    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_ENABLED', True)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_THRESHOLD', 3)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_REWARD_TYPE', 'balance')
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_BALANCE_KOPEKS', 5000)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_DAILY_REWARD_LIMIT', 1)
    monkeypatch.setattr(service, '_get_or_create_progress', AsyncMock(return_value=progress))
    daily_stats, notification_mock = _patch_daily_stats(monkeypatch, service)

    add_balance_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(tap_reward_module, 'add_user_balance', add_balance_mock)

    result = await service.record_taps(db, user, 3)

    assert result.reward_granted is False
    assert result.daily_limit_reached is True
    assert result.taps_until_next == 0
    assert progress.total_taps == 6
    assert progress.reward_count == 1
    assert progress.daily_reward_count == 1
    assert daily_stats.tap_count == 3
    assert daily_stats.reward_count == 0
    notification_mock.assert_not_awaited()
    add_balance_mock.assert_not_awaited()
    db.commit.assert_awaited_once()


async def test_tap_reward_does_not_grant_same_threshold_twice(monkeypatch):
    service = tap_reward_module.TapRewardService()
    progress = _progress(total_taps=3, streak_taps=3, reward_count=1, streak_reward_count=1, daily_reward_count=0)
    user = SimpleNamespace(id=1, balance_kopeks=0)
    db = _db()

    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_ENABLED', True)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_THRESHOLD', 3)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_REWARD_TYPE', 'balance')
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_BALANCE_KOPEKS', 5000)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_DAILY_REWARD_LIMIT', 1)
    monkeypatch.setattr(service, '_get_or_create_progress', AsyncMock(return_value=progress))
    daily_stats, notification_mock = _patch_daily_stats(monkeypatch, service)

    add_balance_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(tap_reward_module, 'add_user_balance', add_balance_mock)

    result = await service.record_taps(db, user, 1)

    assert result.reward_granted is False
    assert result.total_taps == 4
    assert result.progress_taps == 1
    assert result.taps_until_next == 2
    assert progress.reward_count == 1
    assert progress.daily_reward_count == 0
    assert daily_stats.tap_count == 1
    assert daily_stats.reward_count == 0
    notification_mock.assert_not_awaited()
    add_balance_mock.assert_not_awaited()


async def test_tap_reward_continues_to_next_threshold(monkeypatch):
    service = tap_reward_module.TapRewardService()
    progress = _progress(total_taps=3, streak_taps=3, reward_count=1, streak_reward_count=1, daily_reward_count=0)
    user = SimpleNamespace(id=1, balance_kopeks=0)
    db = _db()

    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_ENABLED', True)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_THRESHOLD', 3)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_REWARD_TYPE', 'balance')
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_BALANCE_KOPEKS', 5000)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_DAILY_REWARD_LIMIT', 0)
    monkeypatch.setattr(service, '_get_or_create_progress', AsyncMock(return_value=progress))
    daily_stats, notification_mock = _patch_daily_stats(monkeypatch, service)

    async def add_balance(_db, target_user, amount, **_kwargs):
        target_user.balance_kopeks += amount
        return True

    add_balance_mock = AsyncMock(side_effect=add_balance)
    monkeypatch.setattr(tap_reward_module, 'add_user_balance', add_balance_mock)

    first_result = await service.record_taps(db, user, 2)
    second_result = await service.record_taps(db, user, 1)

    assert first_result.reward_granted is False
    assert first_result.total_taps == 5
    assert first_result.progress_taps == 2
    assert first_result.taps_until_next == 1
    assert second_result.reward_granted is True
    assert second_result.total_taps == 6
    assert second_result.rewards_granted_total == 2
    assert progress.reward_count == 2
    assert daily_stats.tap_count == 3
    assert daily_stats.reward_count == 1
    assert daily_stats.balance_reward_kopeks == 5000
    notification_mock.assert_awaited_once()
    assert add_balance_mock.await_count == 1


async def test_tap_reward_daily_limit_grants_waiting_reward_next_day(monkeypatch):
    service = tap_reward_module.TapRewardService()
    yesterday = datetime.now(UTC).date() - timedelta(days=1)
    progress = _progress(
        total_taps=6,
        streak_taps=6,
        reward_count=1,
        streak_reward_count=1,
        daily_reward_count=1,
        daily_reward_date=yesterday,
    )
    user = SimpleNamespace(id=1, balance_kopeks=0)
    db = _db()

    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_ENABLED', True)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_THRESHOLD', 3)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_REWARD_TYPE', 'balance')
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_BALANCE_KOPEKS', 5000)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_DAILY_REWARD_LIMIT', 1)
    monkeypatch.setattr(service, '_get_or_create_progress', AsyncMock(return_value=progress))
    daily_stats, notification_mock = _patch_daily_stats(monkeypatch, service)

    async def add_balance(_db, target_user, amount, **_kwargs):
        target_user.balance_kopeks += amount
        return True

    add_balance_mock = AsyncMock(side_effect=add_balance)
    monkeypatch.setattr(tap_reward_module, 'add_user_balance', add_balance_mock)

    result = await service.record_taps(db, user, 1)

    assert result.reward_granted is True
    assert result.total_taps == 7
    assert result.rewards_granted_total == 2
    assert progress.reward_count == 2
    assert progress.daily_reward_count == 1
    assert daily_stats.tap_count == 1
    assert daily_stats.reward_count == 1
    assert daily_stats.balance_reward_kopeks == 5000
    notification_mock.assert_awaited_once()
    assert add_balance_mock.await_count == 1


async def test_tap_reward_streak_timeout_resets_progress(monkeypatch):
    service = tap_reward_module.TapRewardService()
    old_tap_at = datetime.now(UTC) - timedelta(seconds=5)
    progress = _progress(total_taps=50, streak_taps=50, last_tap_at=old_tap_at)
    user = SimpleNamespace(id=1, balance_kopeks=0)
    db = _db()

    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_ENABLED', True)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_THRESHOLD', 100)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_REWARD_TYPE', 'balance')
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_BALANCE_KOPEKS', 5000)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_DAILY_REWARD_LIMIT', 1)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_STREAK_TIMEOUT_SECONDS', 1)
    monkeypatch.setattr(service, '_get_or_create_progress', AsyncMock(return_value=progress))
    daily_stats, notification_mock = _patch_daily_stats(monkeypatch, service)

    add_balance_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(tap_reward_module, 'add_user_balance', add_balance_mock)

    result = await service.record_taps(db, user, 1)

    assert result.reward_granted is False
    assert result.total_taps == 51
    assert result.progress_taps == 1
    assert result.taps_until_next == 99
    assert progress.streak_taps == 1
    assert progress.streak_reward_count == 0
    assert daily_stats.tap_count == 1
    assert daily_stats.reward_count == 0
    notification_mock.assert_not_awaited()
    add_balance_mock.assert_not_awaited()


async def test_tap_reward_streak_timeout_prevents_old_threshold_reward(monkeypatch):
    service = tap_reward_module.TapRewardService()
    old_tap_at = datetime.now(UTC) - timedelta(seconds=5)
    progress = _progress(total_taps=100, streak_taps=100, reward_count=0, streak_reward_count=0, last_tap_at=old_tap_at)
    user = SimpleNamespace(id=1, balance_kopeks=0)
    db = _db()

    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_ENABLED', True)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_THRESHOLD', 100)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_REWARD_TYPE', 'balance')
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_BALANCE_KOPEKS', 5000)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_DAILY_REWARD_LIMIT', 1)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_STREAK_TIMEOUT_SECONDS', 1)
    monkeypatch.setattr(service, '_get_or_create_progress', AsyncMock(return_value=progress))
    daily_stats, notification_mock = _patch_daily_stats(monkeypatch, service)

    add_balance_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(tap_reward_module, 'add_user_balance', add_balance_mock)

    result = await service.record_taps(db, user, 1)

    assert result.reward_granted is False
    assert result.total_taps == 101
    assert result.progress_taps == 1
    assert progress.streak_taps == 1
    assert progress.reward_count == 0
    assert daily_stats.tap_count == 1
    assert daily_stats.reward_count == 0
    notification_mock.assert_not_awaited()
    add_balance_mock.assert_not_awaited()


async def test_tap_reward_grants_subscription_days(monkeypatch):
    service = tap_reward_module.TapRewardService()
    progress = _progress()
    user = SimpleNamespace(id=1, balance_kopeks=0, remnawave_uuid='rw-user')
    db = _db()
    end_date = datetime.now(UTC) + timedelta(days=10)
    subscription = SimpleNamespace(id=10, user_id=1, end_date=end_date)

    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_ENABLED', True)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_THRESHOLD', 2)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_REWARD_TYPE', 'subscription_days')
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_SUBSCRIPTION_DAYS', 1)
    monkeypatch.setattr(tap_reward_module.settings, 'TAP_REWARDS_DAILY_REWARD_LIMIT', 0)
    monkeypatch.setattr(service, '_get_or_create_progress', AsyncMock(return_value=progress))
    daily_stats, notification_mock = _patch_daily_stats(monkeypatch, service)
    monkeypatch.setattr(tap_reward_module, 'get_subscription_by_user_id', AsyncMock(return_value=subscription))

    async def extend_subscription(_db, target_subscription, days, **_kwargs):
        target_subscription.end_date += timedelta(days=days)
        return target_subscription

    extend_mock = AsyncMock(side_effect=extend_subscription)
    update_mock = AsyncMock(return_value=object())
    monkeypatch.setattr(tap_reward_module, 'extend_subscription', extend_mock)

    class FakeSubscriptionService:
        update_remnawave_user = update_mock

    monkeypatch.setattr(tap_reward_module, 'SubscriptionService', FakeSubscriptionService)

    result = await service.record_taps(db, user, 2)

    assert result.reward_granted is True
    assert result.reward_type == 'subscription_days'
    assert result.reward_value == 1
    assert result.subscription_end_date == end_date + timedelta(days=1)
    assert progress.total_taps == 2
    assert progress.reward_count == 1
    assert daily_stats.tap_count == 2
    assert daily_stats.reward_count == 1
    assert daily_stats.subscription_reward_days == 1
    notification_mock.assert_awaited_once()
    extend_mock.assert_awaited_once()
    update_mock.assert_awaited_once()
    db.commit.assert_awaited_once()
