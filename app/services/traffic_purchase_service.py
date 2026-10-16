from __future__ import annotations

from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Subscription, TrafficPurchase, User
from app.services.metered_traffic_policy import (
    BYTES_PER_GB,
    block_metered_access,
    cap_metered_usage,
    is_metered_traffic_enabled,
    refresh_metered_usage,
    subscription_allows_special_servers,
)


logger = structlog.get_logger(__name__)


async def remove_expired_traffic_purchases(
    db: AsyncSession,
    subscription: Subscription,
    *,
    now: datetime,
) -> list[TrafficPurchase]:
    """Settle expired quota inside the caller's subscription-row transaction."""
    result = await db.execute(
        select(TrafficPurchase)
        .where(TrafficPurchase.subscription_id == subscription.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    purchases = result.scalars().all()
    expired = [purchase for purchase in purchases if purchase.expires_at <= now]
    if not expired:
        return []
    active = [purchase for purchase in purchases if purchase.expires_at > now]
    total_purchased = sum(purchase.traffic_gb for purchase in purchases)
    old_limit = max(0, int(subscription.traffic_limit_gb or 0))
    base_limit = old_limit - total_purchased
    if old_limit > 0 and base_limit <= 0:
        tariff = subscription.__dict__.get('tariff')
        base_limit = max(0, int(getattr(tariff, 'traffic_limit_gb', 0) or 0)) + max(
            0, int(getattr(subscription, 'device_bonus_traffic_gb', 0) or 0)
        )
        if base_limit <= 0:
            raise ValueError('Cannot determine base traffic quota while expiring temporary packages')

    subscription.purchased_traffic_gb = sum(purchase.traffic_gb for purchase in active)
    subscription.traffic_limit_gb = base_limit + subscription.purchased_traffic_gb if old_limit > 0 else 0
    subscription.traffic_reset_at = min((purchase.expires_at for purchase in active), default=None)
    cap_metered_usage(subscription)
    if (
        subscription_allows_special_servers(subscription)
        and subscription.traffic_limit_gb > 0
        and subscription.traffic_used_gb >= subscription.traffic_limit_gb
    ):
        block_metered_access(subscription)
    for purchase in expired:
        await db.delete(purchase)
    logger.info(
        'Expired traffic packages settled',
        subscription_id=subscription.id,
        expired_gb=sum(purchase.traffic_gb for purchase in expired),
        remaining_purchased_gb=subscription.purchased_traffic_gb,
        traffic_limit_gb=subscription.traffic_limit_gb,
    )
    return expired


async def prepare_metered_traffic_topup(db: AsyncSession, subscription: Subscription) -> None:
    """Account fresh usage against the old allowance before granting new quota."""
    if not is_metered_traffic_enabled():
        return
    await db.refresh(subscription, ['tariff'])
    if not subscription_allows_special_servers(subscription):
        return

    from app.services.remnawave_service import RemnaWaveService

    user = await db.get(User, subscription.user_id)
    if user is None or not user.remnawave_uuid:
        raise RuntimeError('Cannot settle traffic purchase without a panel identity')
    async with RemnaWaveService().get_api_client() as api:
        sampled_at = datetime.now(UTC)
        panel_user = await api.get_user_by_uuid(user.remnawave_uuid)
    if panel_user is None:
        raise RuntimeError('Cannot settle traffic purchase without a current panel user')

    now = datetime.now(UTC)
    await remove_expired_traffic_purchases(db, subscription, now=now)
    used_bytes, _, _ = refresh_metered_usage(
        subscription,
        panel_counter_bytes=panel_user.used_traffic_bytes,
        panel_reset_at=panel_user.last_traffic_reset_at,
        sampled_at=sampled_at,
        now=now,
    )
    if subscription.traffic_limit_gb > 0 and used_bytes >= subscription.traffic_limit_gb * BYTES_PER_GB:
        block_metered_access(subscription)
