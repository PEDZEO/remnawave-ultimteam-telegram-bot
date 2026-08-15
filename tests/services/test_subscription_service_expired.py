from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.services.subscription_service as subscription_service_module
from app.external.remnawave_api import TrafficLimitStrategy, UserStatus
from app.services.subscription_service import SubscriptionService


@pytest.mark.asyncio
async def test_expired_subscription_sync_omits_past_expire_at(monkeypatch: pytest.MonkeyPatch) -> None:
    """Top-up expiry cleanup must be able to sync an already expired subscription."""

    class _Api:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        async def update_user(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(subscription_url='https://example.test/sub', happ_crypto_link='happ://example')

    api = _Api()

    @asynccontextmanager
    async def get_api_client():
        yield api

    db = SimpleNamespace(refresh=AsyncMock(), flush=AsyncMock(), commit=AsyncMock())
    user = SimpleNamespace(
        id=5,
        remnawave_uuid='remna-user-id',
        email='user@example.test',
        full_name='User',
        username='user',
        telegram_id=123,
    )
    subscription = SimpleNamespace(
        id=332,
        user_id=user.id,
        status='active',
        end_date=datetime.now(UTC) - timedelta(days=1),
        traffic_limit_gb=100,
        tariff=None,
        connected_squads=[],
        is_trial=False,
        subscription_url=None,
        subscription_crypto_link=None,
    )

    monkeypatch.setattr(subscription_service_module, 'get_user_by_id', AsyncMock(return_value=user))
    monkeypatch.setattr(
        subscription_service_module, 'get_traffic_reset_strategy', lambda _: TrafficLimitStrategy.NO_RESET
    )
    monkeypatch.setattr(subscription_service_module, 'is_metered_traffic_enabled', lambda: False)
    monkeypatch.setattr(subscription_service_module, 'restore_metered_access_if_available', lambda _: None)
    monkeypatch.setattr(subscription_service_module, 'resolve_hwid_device_limit_for_payload', lambda _: None)
    monkeypatch.setattr(
        subscription_service_module,
        'settings',
        SimpleNamespace(
            DEFAULT_TRAFFIC_RESET_STRATEGY='NO_RESET',
            format_remnawave_user_description=lambda **_: 'description',
        ),
    )

    service = SubscriptionService.__new__(SubscriptionService)
    service.get_api_client = get_api_client
    service._resolve_user_tag = lambda _: None

    updated = await service.update_remnawave_user(db, subscription, commit=False)

    assert updated is not None
    assert api.calls[0]['status'] is UserStatus.DISABLED
    assert 'expire_at' not in api.calls[0]
    db.flush.assert_awaited_once()
