from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.subscription import get_subscription_base_traffic_limit
from app.database.models import Subscription, User
from app.utils.pricing_utils import apply_percentage_discount, get_remaining_months

from .common import get_addon_discount_percent_for_user


def resolve_new_traffic_value(payload) -> int:
    raw_value = payload.traffic if payload.traffic is not None else payload.traffic_gb
    if raw_value is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'validation_error', 'message': 'Traffic amount is required'},
        )

    try:
        new_traffic = int(raw_value)
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'validation_error', 'message': 'Invalid traffic amount'},
        ) from None

    if new_traffic < 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'validation_error', 'message': 'Traffic amount must be non-negative'},
        )

    return new_traffic


def ensure_traffic_update_allowed(new_traffic: int) -> None:
    if settings.is_traffic_topup_blocked():
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={
                'code': 'traffic_fixed',
                'message': 'Traffic cannot be changed for this subscription',
            },
        )

    available_packages: list[int] = []
    for package in settings.get_traffic_packages():
        try:
            gb_value = int(package.get('gb'))
        except (TypeError, ValueError):
            continue
        is_enabled = bool(package.get('enabled', True))
        if package.get('is_active') is False:
            is_enabled = False
        if is_enabled:
            available_packages.append(gb_value)

    if available_packages and new_traffic not in available_packages:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'traffic_unavailable',
                'message': 'Selected traffic package is not available',
            },
        )


def calculate_traffic_upgrade_cost(
    user: User,
    subscription: Subscription,
    new_traffic: int,
) -> tuple[int, int]:
    months_remaining = get_remaining_months(subscription.end_date)
    period_hint_days = months_remaining * 30 if months_remaining > 0 else None
    traffic_discount = get_addon_discount_percent_for_user(user, 'traffic', period_hint_days)

    old_price_per_month = settings.get_traffic_price(get_subscription_base_traffic_limit(subscription))
    new_price_per_month = settings.get_traffic_price(new_traffic)

    discounted_old_per_month, _ = apply_percentage_discount(old_price_per_month, traffic_discount)
    discounted_new_per_month, _ = apply_percentage_discount(new_price_per_month, traffic_discount)

    price_difference_per_month = discounted_new_per_month - discounted_old_per_month
    if price_difference_per_month <= 0:
        return 0, months_remaining

    return price_difference_per_month * months_remaining, months_remaining


async def charge_traffic_upgrade(
    db: AsyncSession,
    user: User,
    subscription: Subscription,
    *,
    new_traffic: int,
    total_price_difference: int,
    months_remaining: int,
) -> None:
    if total_price_difference <= 0:
        return

    from app.database.crud.transaction import create_transaction
    from app.database.crud.user import subtract_user_balance
    from app.database.models import TransactionType

    if getattr(user, 'balance_kopeks', 0) < total_price_difference:
        missing = total_price_difference - getattr(user, 'balance_kopeks', 0)
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                'code': 'insufficient_funds',
                'message': f'Недостаточно средств на балансе. Не хватает {settings.format_price(missing)}',
            },
        )

    current_traffic = get_subscription_base_traffic_limit(subscription)
    description = f'Переключение трафика с {current_traffic}GB на {new_traffic}GB'
    success = await subtract_user_balance(
        db,
        user,
        total_price_difference,
        description,
    )
    if not success:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={
                'code': 'balance_charge_failed',
                'message': 'Failed to charge user balance',
            },
        )

    await create_transaction(
        db=db,
        user_id=user.id,
        type=TransactionType.SUBSCRIPTION_PAYMENT,
        amount_kopeks=total_price_difference,
        description=f'{description} на {months_remaining} мес',
    )
