from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.notification_delivery_service import NotificationDeliveryService, NotificationType


pytestmark = pytest.mark.asyncio


async def test_send_notification_suppresses_unexpected_errors(monkeypatch):
    service = NotificationDeliveryService()
    user = SimpleNamespace(
        id=123,
        status='active',
        telegram_id=999111222,
        email=None,
        email_verified=False,
    )

    async def _raise_unexpected(*args, **kwargs):
        _ = args, kwargs
        raise RuntimeError('unexpected notification failure')

    monkeypatch.setattr(service, '_send_telegram_notification', _raise_unexpected)

    result = await service.send_notification(
        user=user,
        notification_type=NotificationType.BALANCE_TOPUP,
        context={},
        bot=AsyncMock(),
        telegram_message='test',
    )

    assert result is False


async def test_send_notification_delivers_to_telegram_email_and_websocket(monkeypatch):
    service = NotificationDeliveryService()
    user = SimpleNamespace(
        id=321,
        status='active',
        telegram_id=999111222,
        email='user@example.com',
        email_verified=True,
    )
    telegram_delivery = AsyncMock(return_value=True)
    email_delivery = AsyncMock(return_value=True)
    websocket_delivery = AsyncMock(return_value=False)
    monkeypatch.setattr(service, '_send_telegram_notification', telegram_delivery)
    monkeypatch.setattr(service, '_send_email_notification', email_delivery)
    monkeypatch.setattr(service, '_send_websocket_notification', websocket_delivery)
    monkeypatch.setattr(
        'app.config.Settings.are_user_email_notifications_enabled',
        lambda self: True,
    )

    result = await service.send_notification(
        user=user,
        notification_type=NotificationType.WEBHOOK_SUB_BANDWIDTH_THRESHOLD,
        context={'percent': 80},
        bot=AsyncMock(),
        telegram_message='<b>Traffic warning</b>',
    )

    assert result is True
    telegram_delivery.assert_awaited_once()
    email_delivery.assert_awaited_once_with(
        user,
        NotificationType.WEBHOOK_SUB_BANDWIDTH_THRESHOLD,
        {'percent': 80},
        fallback_message='<b>Traffic warning</b>',
    )
    websocket_delivery.assert_awaited_once()


async def test_email_success_is_not_lost_when_telegram_delivery_fails(monkeypatch):
    service = NotificationDeliveryService()
    user = SimpleNamespace(
        id=654,
        status='active',
        telegram_id=999111222,
        email='user@example.com',
        email_verified=True,
    )
    monkeypatch.setattr(service, '_send_telegram_notification', AsyncMock(return_value=False))
    monkeypatch.setattr(service, '_send_email_notification', AsyncMock(return_value=True))
    monkeypatch.setattr(service, '_send_websocket_notification', AsyncMock(return_value=False))
    monkeypatch.setattr(
        'app.config.Settings.are_user_email_notifications_enabled',
        lambda self: True,
    )

    result = await service.send_notification(
        user=user,
        notification_type=NotificationType.BALANCE_TOPUP,
        context={},
        bot=AsyncMock(),
        telegram_message='Balance updated',
    )

    assert result is True


async def test_websocket_delivery_does_not_require_verified_email(monkeypatch):
    service = NotificationDeliveryService()
    user = SimpleNamespace(
        id=777,
        status='active',
        telegram_id=None,
        email=None,
        email_verified=False,
    )
    websocket_delivery = AsyncMock(return_value=True)
    monkeypatch.setattr(service, '_send_websocket_notification', websocket_delivery)

    result = await service.send_notification(
        user=user,
        notification_type=NotificationType.WEBHOOK_SUB_BANDWIDTH_THRESHOLD,
        context={'percent': 80},
    )

    assert result is True
    websocket_delivery.assert_awaited_once()


async def test_blocked_user_can_receive_ban_notification(monkeypatch):
    service = NotificationDeliveryService()
    user = SimpleNamespace(
        id=987,
        status='blocked',
        telegram_id=999111222,
        email=None,
        email_verified=False,
    )
    telegram_delivery = AsyncMock(return_value=True)
    monkeypatch.setattr(service, '_send_telegram_notification', telegram_delivery)

    result = await service.send_notification(
        user=user,
        notification_type=NotificationType.BAN_NOTIFICATION,
        context={'reason': 'Policy violation'},
        bot=AsyncMock(),
        telegram_message='Account blocked',
    )

    assert result is True
    telegram_delivery.assert_awaited_once()
