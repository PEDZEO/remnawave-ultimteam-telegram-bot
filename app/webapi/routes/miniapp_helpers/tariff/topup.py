from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.tariff import get_tariff_by_id
from app.database.models import Subscription, User
from app.services.subscription_service import SubscriptionService
from app.utils.pricing_utils import calculate_prorated_price


async def get_tariff_for_topup(
    db: AsyncSession,
    subscription: Subscription,
):
    tariff_id = getattr(subscription, 'tariff_id', None)
    if not tariff_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'no_tariff',
                'message': 'Subscription has no tariff',
            },
        )

    tariff = await get_tariff_by_id(db, tariff_id)
    if not tariff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                'code': 'tariff_not_found',
                'message': 'Tariff not found',
            },
        )

    return tariff


def validate_topup_package(
    subscription: Subscription,
    tariff,
    package_gb: int,
) -> int:
    if not getattr(tariff, 'traffic_topup_enabled', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                'code': 'traffic_topup_disabled',
                'message': 'Traffic top-up is disabled for this tariff',
            },
        )

    if tariff.traffic_limit_gb == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'unlimited_traffic',
                'message': 'Cannot add traffic to unlimited subscription',
            },
        )

    if (subscription.traffic_limit_gb or 0) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'unlimited_traffic',
                'message': 'Cannot add traffic to unlimited subscription',
            },
        )

    max_topup_limit = getattr(tariff, 'max_topup_traffic_gb', 0) or 0
    if max_topup_limit > 0:
        current_traffic = subscription.traffic_limit_gb or 0
        new_traffic = current_traffic + package_gb
        if new_traffic > max_topup_limit:
            available_gb = max(0, max_topup_limit - current_traffic)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'code': 'topup_limit_exceeded',
                    'message': f'Traffic top-up limit exceeded. Maximum allowed: {max_topup_limit} GB, current: {current_traffic} GB, available: {available_gb} GB',
                    'max_limit_gb': max_topup_limit,
                    'current_gb': current_traffic,
                    'available_gb': available_gb,
                },
            )

    packages = tariff.get_traffic_topup_packages() if hasattr(tariff, 'get_traffic_topup_packages') else {}
    if package_gb not in packages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'invalid_package',
                'message': f'Traffic package {package_gb}GB is not available',
            },
        )

    return int(packages[package_gb])


def calculate_topup_price(
    user: User,
    subscription: Subscription,
    base_price_kopeks: int,
) -> tuple[int, int]:
    traffic_discount_percent = 0
    promo_group = (
        user.get_primary_promo_group()
        if hasattr(user, 'get_primary_promo_group')
        else getattr(user, 'promo_group', None)
    )
    if promo_group and getattr(promo_group, 'apply_discounts_to_addons', True):
        raw_discount = getattr(promo_group, 'traffic_discount_percent', 0) or 0
        traffic_discount_percent = max(0, min(100, int(raw_discount)))

    discounted_price = (
        int(base_price_kopeks * (100 - traffic_discount_percent) / 100)
        if traffic_discount_percent > 0
        else base_price_kopeks
    )
    final_price, _ = calculate_prorated_price(discounted_price, subscription.end_date)
    return int(final_price), traffic_discount_percent


def build_topup_description(package_gb: int, discount_percent: int) -> str:
    if discount_percent > 0:
        return f'Докупка {package_gb} ГБ трафика (скидка {discount_percent}%)'
    return f'Докупка {package_gb} ГБ трафика'


def ensure_topup_balance(user: User, final_price: int) -> None:
    if user.balance_kopeks >= final_price:
        return

    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            'code': 'insufficient_balance',
            'message': 'Insufficient balance',
            'required': final_price,
            'balance': user.balance_kopeks,
        },
    )


async def execute_topup_purchase(
    db: AsyncSession,
    user: User,
    subscription: Subscription,
    *,
    package_gb: int,
    final_price: int,
    description: str,
    logger,
) -> None:
    from app.database.crud.subscription import (
        add_subscription_traffic,
        reactivate_subscription,
    )
    from app.database.crud.transaction import create_transaction, emit_transaction_side_effects
    from app.database.crud.user import subtract_user_balance
    from app.database.models import TransactionType

    success = await subtract_user_balance(db, user, final_price, description, commit=False)
    if not success:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'code': 'balance_error',
                'message': 'Failed to subtract balance',
            },
        )

    await add_subscription_traffic(db, subscription, package_gb, commit=False)
    # Reactivate DISABLED/EXPIRED subscriptions after successful top-up.
    await reactivate_subscription(db, subscription, commit=False)

    transaction = await create_transaction(
        db,
        user_id=user.id,
        type=TransactionType.SUBSCRIPTION_PAYMENT,
        amount_kopeks=final_price,
        description=description,
        commit=False,
    )
    await db.commit()
    await emit_transaction_side_effects(
        db,
        transaction,
        user_id=user.id,
        type=TransactionType.SUBSCRIPTION_PAYMENT,
        amount_kopeks=final_price,
        description=description,
    )

    try:
        service = SubscriptionService()
        await service.update_remnawave_user(db, subscription)
        if getattr(user, 'remnawave_uuid', None) and subscription.status == 'active':
            await service.enable_remnawave_user(user.remnawave_uuid)
    except Exception as error:
        logger.error('Ошибка синхронизации с RemnaWave при докупке трафика', error=error)
