from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.database.crud.transaction import _send_external_deposit_email_copy
from app.database.models import PaymentMethod, TransactionType
from app.services.notification_delivery_service import NotificationType, notification_delivery_service


pytestmark = pytest.mark.asyncio


class _SessionStub:
    def __init__(self, user):
        self.user = user
        self.get = AsyncMock(return_value=user)


async def test_external_deposit_sends_one_email_copy(monkeypatch):
    user = SimpleNamespace(id=7, email='user@example.com', email_verified=True, status='active')
    db = _SessionStub(user)
    delivery = AsyncMock(return_value=True)
    monkeypatch.setattr(notification_delivery_service, 'send_email_copy', delivery)

    await _send_external_deposit_email_copy(
        db,
        user_id=user.id,
        amount_kopeks=12500,
        type=TransactionType.DEPOSIT,
        payment_method=PaymentMethod.YOOKASSA,
        is_completed=True,
    )

    delivery.assert_awaited_once()
    call = delivery.await_args.kwargs
    assert call['user'] is user
    assert call['notification_type'] is NotificationType.PAYMENT_RECEIVED
    assert call['context']['amount_kopeks'] == 12500
    assert call['context']['payment_method'] == PaymentMethod.YOOKASSA.value


@pytest.mark.parametrize('payment_method', [None, PaymentMethod.MANUAL, PaymentMethod.BALANCE])
async def test_internal_deposit_does_not_send_external_payment_receipt(monkeypatch, payment_method):
    db = _SessionStub(SimpleNamespace(id=8))
    delivery = AsyncMock(return_value=True)
    monkeypatch.setattr(notification_delivery_service, 'send_email_copy', delivery)

    await _send_external_deposit_email_copy(
        db,
        user_id=8,
        amount_kopeks=1000,
        type=TransactionType.DEPOSIT,
        payment_method=payment_method,
        is_completed=True,
    )

    delivery.assert_not_awaited()
