from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import MissingGreenlet

from app.config import settings
from app.services import subscription_auto_purchase_service as service


class LazySubscriptionUser(SimpleNamespace):
    @property
    def subscription(self):
        raise MissingGreenlet('subscription was expired by payment refresh')


@pytest.mark.asyncio
@pytest.mark.parametrize('status', [None, 'active'])
@pytest.mark.parametrize(
    ('mode', 'handler_name'),
    [
        ('extend', '_auto_extend_subscription'),
        ('tariff_purchase', '_auto_purchase_tariff'),
        ('daily_tariff_purchase', '_auto_purchase_daily_tariff'),
        ('add_devices', '_auto_add_devices'),
        ('add_traffic', '_auto_add_traffic'),
    ],
)
async def test_auto_purchase_queries_subscription_without_lazy_loading(monkeypatch, status, mode, handler_name):
    monkeypatch.setattr(settings, 'AUTO_PURCHASE_AFTER_TOPUP_ENABLED', True)
    user = LazySubscriptionUser(id=42, telegram_id=4242)
    db = object()
    cart = {'cart_mode': mode, 'total_price': 1000}
    subscription = SimpleNamespace(status=status) if status else None
    lookup = AsyncMock(return_value=subscription)
    handler = AsyncMock(return_value=True)
    monkeypatch.setattr('app.database.crud.subscription.get_subscription_by_user_id', lookup)
    monkeypatch.setattr('app.database.crud.transaction.get_user_transactions', AsyncMock(return_value=[]))
    monkeypatch.setattr(service.user_cart_service, 'get_user_cart', AsyncMock(return_value=cart))
    monkeypatch.setattr(service, handler_name, handler)

    assert await service.auto_purchase_saved_cart_after_topup(db, user) is True

    lookup.assert_awaited_once_with(db, user.id)
    handler.assert_awaited_once_with(db, user, cart, bot=None)


@pytest.mark.asyncio
async def test_auto_purchase_keeps_disabled_subscription_guard_with_expired_relationship(monkeypatch):
    monkeypatch.setattr(settings, 'AUTO_PURCHASE_AFTER_TOPUP_ENABLED', True)
    user = LazySubscriptionUser(id=42, telegram_id=4242)
    cart = {'cart_mode': 'tariff_purchase', 'total_price': 1000}
    handler = AsyncMock()
    delete_cart = AsyncMock()
    clear_draft = AsyncMock()
    monkeypatch.setattr(
        'app.database.crud.subscription.get_subscription_by_user_id',
        AsyncMock(return_value=SimpleNamespace(status='disabled')),
    )
    monkeypatch.setattr(service.user_cart_service, 'get_user_cart', AsyncMock(return_value=cart))
    monkeypatch.setattr(service.user_cart_service, 'delete_user_cart', delete_cart)
    monkeypatch.setattr(service, 'clear_subscription_checkout_draft', clear_draft)
    monkeypatch.setattr(service, '_auto_purchase_tariff', handler)

    assert await service.auto_purchase_saved_cart_after_topup(object(), user) is False

    handler.assert_not_awaited()
    delete_cart.assert_awaited_once_with(user.id)
    clear_draft.assert_awaited_once_with(user.id)


@pytest.mark.asyncio
async def test_auto_purchase_does_not_charge_when_subscription_lookup_fails(monkeypatch):
    monkeypatch.setattr(settings, 'AUTO_PURCHASE_AFTER_TOPUP_ENABLED', True)
    user = SimpleNamespace(id=42, telegram_id=4242, subscription=SimpleNamespace(status='active'))
    handler = AsyncMock()
    delete_cart = AsyncMock()
    monkeypatch.setattr(
        'app.database.crud.subscription.get_subscription_by_user_id',
        AsyncMock(side_effect=RuntimeError('database unavailable')),
    )
    monkeypatch.setattr(
        service.user_cart_service,
        'get_user_cart',
        AsyncMock(return_value={'cart_mode': 'tariff_purchase', 'total_price': 1000}),
    )
    monkeypatch.setattr(service.user_cart_service, 'delete_user_cart', delete_cart)
    monkeypatch.setattr(service, '_auto_purchase_tariff', handler)

    with pytest.raises(RuntimeError, match='database unavailable'):
        await service.auto_purchase_saved_cart_after_topup(object(), user)

    handler.assert_not_awaited()
    delete_cart.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('status', ['active', 'disabled', 'expired', 'limited'])
@pytest.mark.parametrize(
    'handler_name', ['try_auto_extend_expired_after_topup', 'try_resume_disabled_daily_after_topup']
)
async def test_automatic_renewal_status_guards_do_not_raise_name_error(monkeypatch, status, handler_name):
    subscription = SimpleNamespace(status=status, is_trial=True, is_daily_tariff=False)
    monkeypatch.setattr(
        'app.database.crud.subscription.get_subscription_by_user_id', AsyncMock(return_value=subscription)
    )
    user = SimpleNamespace(id=42, telegram_id=4242)

    assert await getattr(service, handler_name)(object(), user) is False
