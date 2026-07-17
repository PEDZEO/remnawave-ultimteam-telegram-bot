from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.database.crud import subscription as subscription_crud
from app.services import remnawave_service as remnawave_service_module
from app.services.remnawave_service import RemnaWaveService


@pytest.mark.asyncio
async def test_panel_sync_reuses_preloaded_subscription(monkeypatch: pytest.MonkeyPatch) -> None:
    lookup = AsyncMock(side_effect=AssertionError('unexpected subscription lookup'))
    monkeypatch.setattr(subscription_crud, 'get_subscription_by_user_id', lookup)
    monkeypatch.setattr(subscription_crud, 'is_recently_updated_by_webhook', lambda subscription: False)
    monkeypatch.setattr(remnawave_service_module, 'is_metered_traffic_enabled', lambda: True)

    service = RemnaWaveService()
    expires_at = service._now_utc() + timedelta(days=30)
    user = SimpleNamespace(id=1, telegram_id=123456)
    subscription = SimpleNamespace(
        id=10,
        end_date=expires_at,
        status='active',
        traffic_used_gb=2.0,
        traffic_limit_gb=35,
        device_limit=2,
        remnawave_short_uuid='old-short-id',
        subscription_url='https://old.example',
        subscription_crypto_link='old-link',
        connected_squads=['old-squad'],
    )
    panel_user = {
        'status': 'ACTIVE',
        'expireAt': expires_at.isoformat(),
        'usedTrafficBytes': 3 * 1024**3,
        'trafficLimitBytes': 0,
        'hwidDeviceLimit': 4,
        'shortUuid': 'new-short-id',
        'subscriptionUrl': 'https://new.example',
        'subscriptionCryptoLink': 'new-link',
        'activeInternalSquads': [{'uuid': 'new-squad'}],
    }

    await service._update_subscription_from_panel_data(
        SimpleNamespace(),
        user,
        panel_user,
        subscription=subscription,
    )

    lookup.assert_not_awaited()
    assert subscription.device_limit == 4
    assert subscription.remnawave_short_uuid == 'new-short-id'
    assert subscription.connected_squads == ['new-squad']
