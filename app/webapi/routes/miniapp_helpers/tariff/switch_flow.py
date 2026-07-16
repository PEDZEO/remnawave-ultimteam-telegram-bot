from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.server_squad import get_all_server_squads
from app.database.models import TrafficPurchase

from .switch import calculate_tariff_switch_cost


@dataclass(slots=True)
class TariffSwitchPricing:
    upgrade_cost: int
    is_upgrade: bool
    switching_from_daily: bool
    new_period_days: int


def calculate_switch_pricing(
    current_tariff,
    new_tariff,
    remaining_days: int,
    promo_group,
    user,
) -> TariffSwitchPricing:
    current_is_daily = getattr(current_tariff, 'is_daily', False) if current_tariff else False
    new_is_daily = getattr(new_tariff, 'is_daily', False)
    switching_from_daily = current_is_daily and not new_is_daily

    if switching_from_daily:
        min_period_days = 30
        min_period_price = 0
        if new_tariff.period_prices:
            min_period_days = min(int(key) for key in new_tariff.period_prices.keys())
            min_period_price = new_tariff.period_prices.get(str(min_period_days), 0)
        return TariffSwitchPricing(
            upgrade_cost=int(min_period_price),
            is_upgrade=min_period_price > 0,
            switching_from_daily=True,
            new_period_days=int(min_period_days),
        )

    upgrade_cost, is_upgrade = calculate_tariff_switch_cost(
        current_tariff,
        new_tariff,
        remaining_days,
        promo_group,
        user,
    )
    return TariffSwitchPricing(
        upgrade_cost=int(upgrade_cost),
        is_upgrade=bool(is_upgrade),
        switching_from_daily=False,
        new_period_days=0,
    )


def ensure_switch_balance(user, upgrade_cost: int) -> None:
    if user.balance_kopeks >= upgrade_cost:
        return

    missing = upgrade_cost - user.balance_kopeks
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            'code': 'insufficient_funds',
            'message': f'Недостаточно средств. Не хватает {settings.format_price(missing)}',
            'missing_amount': missing,
        },
    )


def build_switch_charge_description(
    *,
    new_tariff_name: str,
    switching_from_daily: bool,
    new_period_days: int,
    remaining_days: int,
) -> str:
    if switching_from_daily:
        return f"Переход с суточного на тариф '{new_tariff_name}' ({new_period_days} дней)"
    return f"Переход на тариф '{new_tariff_name}' (доплата за {remaining_days} дней)"


def build_switch_result_message(language: str, tariff_name: str, upgrade_cost: int) -> str:
    if upgrade_cost > 0:
        if language == 'ru':
            return f"Тариф изменён на '{tariff_name}'. Списано {settings.format_price(upgrade_cost)}"
        return f"Switched to '{tariff_name}'. Charged {settings.format_price(upgrade_cost)}"

    if language == 'ru':
        return f"Тариф изменён на '{tariff_name}'"
    return f"Switched to '{tariff_name}'"


async def apply_tariff_switch_to_subscription(
    db: AsyncSession,
    subscription,
    current_tariff,
    new_tariff,
    *,
    new_period_days: int,
    logger,
) -> None:
    from app.database.crud.subscription import calc_device_limit_on_tariff_switch
    from app.services.device_traffic_bonus import rebuild_traffic_with_device_bonus

    squads = await resolve_tariff_squads(db, new_tariff)

    subscription.tariff_id = new_tariff.id
    subscription.traffic_limit_gb = new_tariff.traffic_limit_gb
    subscription.device_limit = calc_device_limit_on_tariff_switch(
        current_device_limit=subscription.device_limit,
        old_tariff_device_limit=current_tariff.device_limit if current_tariff else None,
        new_tariff_device_limit=new_tariff.device_limit,
        max_device_limit=new_tariff.max_device_limit,
    )
    subscription.connected_squads = squads
    await db.execute(sql_delete(TrafficPurchase).where(TrafficPurchase.subscription_id == subscription.id))
    subscription.purchased_traffic_gb = 0
    subscription.traffic_reset_at = None
    rebuild_traffic_with_device_bonus(
        subscription,
        new_tariff,
        new_tariff.traffic_limit_gb,
        preserve_purchased_traffic=False,
    )
    if settings.RESET_TRAFFIC_ON_TARIFF_SWITCH:
        subscription.traffic_used_gb = 0.0

    new_is_daily = getattr(new_tariff, 'is_daily', False)
    old_is_daily = getattr(current_tariff, 'is_daily', False)

    if new_is_daily:
        subscription.is_daily_paused = False
        subscription.last_daily_charge_at = datetime.now(UTC)
        subscription.end_date = datetime.now(UTC) + timedelta(days=1)
        logger.info('🔄 Смена на суточный тариф: установлены daily поля, end_date', end_date=subscription.end_date)
        return

    if old_is_daily and not new_is_daily:
        subscription.is_daily_paused = False
        subscription.last_daily_charge_at = None
        if new_period_days > 0:
            subscription.end_date = datetime.now(UTC) + timedelta(days=new_period_days)
            logger.info(
                '🔄 Смена с суточного на периодный тариф: end_date= ( дней)',
                end_date=subscription.end_date,
                new_period_days=new_period_days,
            )
            return
        logger.info('🔄 Смена с суточного на обычный тариф: очищены daily поля')


async def resolve_tariff_squads(db: AsyncSession, tariff) -> list[str]:
    squads = list(tariff.allowed_squads or [])
    if squads:
        return squads

    all_servers, _ = await get_all_server_squads(db, available_only=True)
    return [server.squad_uuid for server in all_servers if server.squad_uuid]


async def execute_switch_charge(
    db: AsyncSession,
    user,
    *,
    upgrade_cost: int,
    description: str,
) -> None:
    from app.database.crud.transaction import create_transaction
    from app.database.crud.user import subtract_user_balance
    from app.database.models import TransactionType

    success = await subtract_user_balance(db, user, upgrade_cost, description)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'code': 'balance_error', 'message': 'Failed to charge balance'},
        )

    await create_transaction(
        db=db,
        user_id=user.id,
        type=TransactionType.SUBSCRIPTION_PAYMENT,
        amount_kopeks=upgrade_cost,
        description=description,
    )
