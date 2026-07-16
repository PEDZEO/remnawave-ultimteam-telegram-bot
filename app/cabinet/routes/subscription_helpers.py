"""Shared helper functions for cabinet subscription routes."""

from datetime import UTC, datetime, timedelta
from typing import Any

from app.config import settings
from app.database.models import Subscription, User
from app.services.metered_traffic_policy import is_metered_traffic_enabled

from ..schemas.subscription import ServerInfo, SubscriptionData, SubscriptionResponse


def get_addon_discount_percent(
    user: User,
    category: str,
    period_days: int | None = None,
) -> int:
    """Get addon discount percent for user from promo group."""
    promo_group = (
        user.get_primary_promo_group()
        if hasattr(user, 'get_primary_promo_group')
        else getattr(user, 'promo_group', None)
    )
    if promo_group is None:
        return 0

    if not getattr(promo_group, 'apply_discounts_to_addons', True):
        return 0

    try:
        return user.get_promo_discount(category, period_days)
    except AttributeError:
        return 0


def apply_addon_discount(
    user: User,
    category: str,
    amount: int,
    period_days: int | None = None,
) -> dict[str, int]:
    """Apply addon discount to amount."""
    percent = get_addon_discount_percent(user, category, period_days)
    if percent <= 0 or amount <= 0:
        return {'discounted': amount, 'discount': 0, 'percent': 0}

    discount_value = int(amount * percent / 100)
    discounted_amount = amount - discount_value
    return {
        'discounted': discounted_amount,
        'discount': discount_value,
        'percent': percent,
    }


def get_period_discount_percent(user: User, period_days: int | None = None) -> int:
    """Get period discount percent for tariff switch calculations."""
    promo_group = (
        user.get_primary_promo_group()
        if hasattr(user, 'get_primary_promo_group')
        else getattr(user, 'promo_group', None)
    )
    if promo_group is None:
        return 0

    try:
        return user.get_promo_discount('period', period_days)
    except AttributeError:
        return 0


def subscription_to_response(
    subscription: Subscription,
    servers: list[ServerInfo] | None = None,
    tariff_name: str | None = None,
    traffic_purchases: list[dict[str, Any]] | None = None,
) -> SubscriptionData:
    """Convert Subscription model to response."""
    now = datetime.now(UTC)

    actual_status = subscription.actual_status
    is_expired = actual_status == 'expired'
    is_active = actual_status in ('active', 'trial')

    days_left = 0
    hours_left = 0
    minutes_left = 0
    time_left_display = ''

    if subscription.end_date and not is_expired:
        time_delta = subscription.end_date - now
        total_seconds = max(0, int(time_delta.total_seconds()))

        days_left = total_seconds // 86400
        remaining_seconds = total_seconds % 86400
        hours_left = remaining_seconds // 3600
        minutes_left = (remaining_seconds % 3600) // 60

        if days_left > 0:
            time_left_display = f'{days_left}d {hours_left}h'
        elif hours_left > 0:
            time_left_display = f'{hours_left}h {minutes_left}m'
        elif minutes_left > 0:
            time_left_display = f'{minutes_left}m'
        else:
            time_left_display = '0m'
    else:
        time_left_display = '0m'

    traffic_limit_gb = subscription.traffic_limit_gb or 0
    traffic_used_gb = subscription.traffic_used_gb or 0.0

    if traffic_limit_gb > 0:
        traffic_used_percent = min(100, (traffic_used_gb / traffic_limit_gb) * 100)
    else:
        traffic_used_percent = 0

    is_daily_paused = getattr(subscription, 'is_daily_paused', False) or False
    tariff_id = getattr(subscription, 'tariff_id', None)

    is_daily = False
    daily_price_kopeks = None

    if hasattr(subscription, 'is_daily_tariff'):
        is_daily = subscription.is_daily_tariff
    elif tariff_id and hasattr(subscription, 'tariff') and subscription.tariff:
        is_daily = getattr(subscription.tariff, 'is_daily', False)

    traffic_reset_mode = None
    if tariff_id and hasattr(subscription, 'tariff') and subscription.tariff:
        daily_price_kopeks = getattr(subscription.tariff, 'daily_price_kopeks', None)
        if not tariff_name:
            tariff_name = getattr(subscription.tariff, 'name', None)
        traffic_reset_mode = (
            getattr(subscription.tariff, 'traffic_reset_mode', None) or settings.DEFAULT_TRAFFIC_RESET_STRATEGY
        )

    next_daily_charge_at = None
    if is_daily and not is_daily_paused:
        last_charge = getattr(subscription, 'last_daily_charge_at', None)
        if last_charge:
            next_charge = last_charge + timedelta(days=1)
            # Если время списания уже прошло, скрываем stale-значение
            # и даем DailySubscriptionService обработать подписку.
            if next_charge > now:
                next_daily_charge_at = next_charge

    hide_link = settings.should_hide_subscription_link()
    metered_enabled = is_metered_traffic_enabled()
    metered_remaining_gb = None
    if metered_enabled and traffic_limit_gb > 0:
        metered_remaining_gb = round(max(0.0, traffic_limit_gb - traffic_used_gb), 2)

    return SubscriptionResponse(
        id=subscription.id,
        status=actual_status,
        is_trial=subscription.is_trial or actual_status == 'trial',
        start_date=subscription.start_date,
        end_date=subscription.end_date,
        days_left=days_left,
        hours_left=hours_left,
        minutes_left=minutes_left,
        time_left_display=time_left_display,
        traffic_limit_gb=traffic_limit_gb,
        traffic_used_gb=round(traffic_used_gb, 2),
        traffic_used_percent=round(traffic_used_percent, 1),
        device_limit=subscription.device_limit or 0,
        connected_squads=subscription.connected_squads or [],
        servers=servers or [],
        autopay_enabled=subscription.autopay_enabled or False,
        autopay_days_before=subscription.autopay_days_before or 3,
        subscription_url=subscription.subscription_url,
        hide_subscription_link=hide_link,
        is_active=is_active,
        is_expired=is_expired,
        traffic_purchases=traffic_purchases or [],
        is_daily=is_daily,
        is_daily_paused=is_daily_paused,
        daily_price_kopeks=daily_price_kopeks,
        next_daily_charge_at=next_daily_charge_at,
        tariff_id=tariff_id,
        tariff_name=tariff_name,
        traffic_reset_mode=traffic_reset_mode,
        metered_traffic_enabled=metered_enabled,
        metered_access_blocked=bool(getattr(subscription, 'metered_access_blocked', False)),
        metered_server_label=(settings.ULTIMA_METERED_SERVER_LABEL if metered_enabled else None),
        metered_traffic_remaining_gb=metered_remaining_gb,
        standard_traffic_unlimited=metered_enabled,
    )
