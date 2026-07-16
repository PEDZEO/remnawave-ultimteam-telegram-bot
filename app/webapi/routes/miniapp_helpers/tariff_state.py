from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.tariff import get_tariff_by_id
from app.services.metered_traffic_policy import (
    get_customer_squad_uuids,
    is_metered_traffic_enabled,
    tariff_allows_special_servers,
)
from app.webapi.schemas.miniapp import MiniAppCurrentTariff, MiniAppTrafficTopupPackage

from ..miniapp_format_helpers import format_traffic_limit_label
from .tariff.base import get_tariff_monthly_price


def is_trial_available_for_user(user) -> bool:
    if settings.TRIAL_DURATION_DAYS <= 0:
        return False

    if settings.is_trial_disabled_for_user(getattr(user, 'auth_type', 'telegram')):
        return False

    if getattr(user, 'has_had_paid_subscription', False):
        return False

    subscription = getattr(user, 'subscription', None)
    if subscription is not None:
        return False

    return True


async def get_current_tariff_model(db: AsyncSession, subscription, user=None) -> MiniAppCurrentTariff | None:
    """Возвращает модель текущего тарифа пользователя."""
    if not subscription or not getattr(subscription, 'tariff_id', None):
        return None

    tariff = await get_tariff_by_id(db, subscription.tariff_id)
    if not tariff:
        return None

    servers_count = len(get_customer_squad_uuids(tariff.allowed_squads))

    # Получаем скидку на трафик из промогруппы
    traffic_discount_percent = 0
    promo_group = (
        (
            user.get_primary_promo_group()
            if hasattr(user, 'get_primary_promo_group')
            else getattr(user, 'promo_group', None)
        )
        if user
        else None
    )
    if promo_group:
        apply_to_addons = getattr(promo_group, 'apply_discounts_to_addons', True)
        if apply_to_addons:
            traffic_discount_percent = max(0, min(100, int(getattr(promo_group, 'traffic_discount_percent', 0) or 0)))

    # Лимит докупки трафика
    max_topup_traffic_gb = getattr(tariff, 'max_topup_traffic_gb', 0) or 0
    current_subscription_traffic = subscription.traffic_limit_gb or 0

    # Рассчитываем доступный лимит докупки
    available_topup_gb = None
    if max_topup_traffic_gb > 0:
        available_topup_gb = max(0, max_topup_traffic_gb - current_subscription_traffic)

    # Пакеты докупки трафика
    traffic_topup_enabled = (
        getattr(tariff, 'traffic_topup_enabled', False)
        and tariff.traffic_limit_gb > 0
        and (not is_metered_traffic_enabled() or tariff_allows_special_servers(tariff))
    )
    traffic_topup_packages = []

    if traffic_topup_enabled and hasattr(tariff, 'get_traffic_topup_packages'):
        packages = tariff.get_traffic_topup_packages()
        for gb in sorted(packages.keys()):
            # Фильтруем пакеты, которые превышают доступный лимит
            if available_topup_gb is not None and gb > available_topup_gb:
                continue

            base_price = packages[gb]
            # Применяем скидку
            if traffic_discount_percent > 0:
                discounted_price = int(base_price * (100 - traffic_discount_percent) / 100)
                traffic_topup_packages.append(
                    MiniAppTrafficTopupPackage(
                        gb=gb,
                        price_kopeks=discounted_price,
                        price_label=settings.format_price(discounted_price),
                        original_price_kopeks=base_price,
                        original_price_label=settings.format_price(base_price),
                        discount_percent=traffic_discount_percent,
                    )
                )
            else:
                traffic_topup_packages.append(
                    MiniAppTrafficTopupPackage(
                        gb=gb,
                        price_kopeks=base_price,
                        price_label=settings.format_price(base_price),
                    )
                )

    # Если нет доступных пакетов из-за лимита - отключаем докупку
    if traffic_topup_enabled and not traffic_topup_packages and available_topup_gb == 0:
        traffic_topup_enabled = False

    monthly_price = get_tariff_monthly_price(tariff)

    # Применяем скидку промогруппы для 30-дневного периода
    if promo_group:
        raw_discounts = getattr(promo_group, 'period_discounts', None) or {}
        for key, value in raw_discounts.items():
            try:
                if int(key) == 30:
                    discount = max(0, min(100, int(value)))
                    monthly_price = int(monthly_price * (100 - discount) / 100)
                    break
            except (TypeError, ValueError):
                pass

    return MiniAppCurrentTariff(
        id=tariff.id,
        name=tariff.name,
        description=tariff.description,
        tier_level=tariff.tier_level,
        traffic_limit_gb=tariff.traffic_limit_gb,
        traffic_limit_label=format_traffic_limit_label(tariff.traffic_limit_gb),
        is_unlimited_traffic=tariff.traffic_limit_gb == 0,
        device_limit=tariff.device_limit,
        servers_count=servers_count,
        monthly_price_kopeks=monthly_price,
        traffic_topup_enabled=traffic_topup_enabled,
        traffic_topup_packages=traffic_topup_packages,
        max_topup_traffic_gb=max_topup_traffic_gb,
        available_topup_gb=available_topup_gb,
    )


async def build_current_tariff_model(db: AsyncSession, tariff, promo_group=None) -> MiniAppCurrentTariff:
    """Создаёт модель текущего тарифа."""
    servers_count = len(get_customer_squad_uuids(tariff.allowed_squads))
    monthly_price = get_tariff_monthly_price(tariff)

    # Применяем скидку промогруппы для 30-дневного периода
    if promo_group:
        raw_discounts = getattr(promo_group, 'period_discounts', None) or {}
        for key, value in raw_discounts.items():
            try:
                if int(key) == 30:
                    discount = max(0, min(100, int(value)))
                    monthly_price = int(monthly_price * (100 - discount) / 100)
                    break
            except (TypeError, ValueError):
                pass

    # Суточный тариф
    is_daily = getattr(tariff, 'is_daily', False)
    daily_price_kopeks = getattr(tariff, 'daily_price_kopeks', 0) if is_daily else 0
    daily_price_label = (
        settings.format_price(daily_price_kopeks) + '/день' if is_daily and daily_price_kopeks > 0 else None
    )

    return MiniAppCurrentTariff(
        id=tariff.id,
        name=tariff.name,
        description=tariff.description,
        tier_level=tariff.tier_level,
        traffic_limit_gb=tariff.traffic_limit_gb,
        traffic_limit_label=format_traffic_limit_label(tariff.traffic_limit_gb),
        is_unlimited_traffic=tariff.traffic_limit_gb == 0,
        device_limit=tariff.device_limit,
        servers_count=servers_count,
        monthly_price_kopeks=monthly_price,
        is_daily=is_daily,
        daily_price_kopeks=daily_price_kopeks,
        daily_price_label=daily_price_label,
    )
