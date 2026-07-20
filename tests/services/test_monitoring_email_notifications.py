from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.monitoring_service import MonitoringService
from app.services.notification_delivery_service import notification_delivery_service


pytestmark = pytest.mark.asyncio


async def test_expired_subscription_uses_unified_delivery(monkeypatch):
    bot = AsyncMock()
    service = MonitoringService(bot=bot)
    user = SimpleNamespace(id=9, telegram_id=123456, language='ru')
    delivery = AsyncMock(return_value=True)
    monkeypatch.setattr(notification_delivery_service, 'notify_subscription_expired', delivery)

    result = await service._send_subscription_expired_notification(user)

    assert result is True
    delivery.assert_awaited_once()
    call = delivery.await_args.kwargs
    assert call['user'] is user
    assert call['bot'] is bot
    assert 'Подписка истекла' in call['telegram_message']
