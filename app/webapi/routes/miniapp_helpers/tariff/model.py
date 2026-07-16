from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.server_squad import get_server_squad_by_uuid
from app.services.metered_traffic_policy import get_customer_squad_uuids
from app.utils.pricing_utils import format_period_description
from app.webapi.routes.miniapp_format_helpers import format_traffic_limit_label
from app.webapi.schemas.miniapp import (
    MiniAppConnectedServer,
    MiniAppTariff,
    MiniAppTariffPeriod,
)

from .switch import calculate_tariff_switch_cost


async def build_tariff_model(
    db: AsyncSession,
    tariff,
    current_tariff_id: int | None = None,
    promo_group=None,
    current_tariff=None,
    remaining_days: int = 0,
    user=None,
) -> MiniAppTariff:
    servers: list[MiniAppConnectedServer] = []
    servers_count = 0

    customer_squads = get_customer_squad_uuids(tariff.allowed_squads)
    if customer_squads:
        servers_count = len(customer_squads)
        for squad_uuid in customer_squads[:5]:
            server = await get_server_squad_by_uuid(db, squad_uuid)
            if server:
                servers.append(
                    MiniAppConnectedServer(
                        uuid=squad_uuid,
                        name=server.display_name or squad_uuid[:8],
                    )
                )

    period_discounts: dict[int, int] = {}
    if promo_group:
        raw_discounts = getattr(promo_group, 'period_discounts', None) or {}
        for key, value in raw_discounts.items():
            try:
                period_discounts[int(key)] = max(0, min(100, int(value)))
            except (TypeError, ValueError):
                continue

    periods: list[MiniAppTariffPeriod] = []
    if tariff.period_prices:
        for period_str, original_price_kopeks in sorted(tariff.period_prices.items(), key=lambda item: int(item[0])):
            period_days = int(period_str)
            discount_percent = period_discounts.get(period_days, 0)
            if discount_percent > 0:
                price_kopeks = int(original_price_kopeks * (100 - discount_percent) / 100)
            else:
                price_kopeks = original_price_kopeks

            months = max(1, period_days // 30)
            per_month = price_kopeks // months if months > 0 else price_kopeks
            periods.append(
                MiniAppTariffPeriod(
                    days=period_days,
                    months=months,
                    label=format_period_description(period_days),
                    price_kopeks=price_kopeks,
                    price_label=settings.format_price(price_kopeks),
                    price_per_month_kopeks=per_month,
                    price_per_month_label=settings.format_price(per_month),
                    original_price_kopeks=original_price_kopeks if discount_percent > 0 else None,
                    original_price_label=settings.format_price(original_price_kopeks) if discount_percent > 0 else None,
                    discount_percent=discount_percent,
                )
            )

    switch_cost_kopeks = None
    switch_cost_label = None
    is_upgrade = None
    is_switch_free = None

    if current_tariff and current_tariff.id != tariff.id:
        current_is_daily = getattr(current_tariff, 'is_daily', False)
        new_is_daily = getattr(tariff, 'is_daily', False)

        if current_is_daily and not new_is_daily:
            min_period_price = min((p.price_kopeks for p in periods), default=None)
            if min_period_price and min_period_price > 0:
                switch_cost_kopeks = min_period_price
                switch_cost_label = settings.format_price(min_period_price)
                is_upgrade = True
                is_switch_free = False
        elif remaining_days > 0:
            cost, upgrade = calculate_tariff_switch_cost(
                current_tariff,
                tariff,
                remaining_days,
                promo_group,
                user,
            )
            switch_cost_kopeks = cost
            switch_cost_label = settings.format_price(cost) if cost > 0 else None
            is_upgrade = upgrade
            is_switch_free = cost == 0

    is_daily = getattr(tariff, 'is_daily', False)
    daily_price_kopeks = getattr(tariff, 'daily_price_kopeks', 0) if is_daily else 0
    daily_price_label = (
        settings.format_price(daily_price_kopeks) + '/день' if is_daily and daily_price_kopeks > 0 else None
    )

    return MiniAppTariff(
        id=tariff.id,
        name=tariff.name,
        description=tariff.description,
        tier_level=tariff.tier_level,
        traffic_limit_gb=tariff.traffic_limit_gb,
        traffic_limit_label=format_traffic_limit_label(tariff.traffic_limit_gb),
        is_unlimited_traffic=tariff.traffic_limit_gb == 0,
        device_limit=tariff.device_limit,
        servers_count=servers_count,
        servers=servers,
        periods=periods,
        is_current=current_tariff_id == tariff.id if current_tariff_id else False,
        is_available=tariff.is_active,
        switch_cost_kopeks=switch_cost_kopeks,
        switch_cost_label=switch_cost_label,
        is_upgrade=is_upgrade,
        is_switch_free=is_switch_free,
        is_daily=is_daily,
        daily_price_kopeks=daily_price_kopeks,
        daily_price_label=daily_price_label,
    )
