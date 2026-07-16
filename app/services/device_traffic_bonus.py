from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Subscription, Tariff


def calculate_device_traffic_bonus(tariff: Tariff | None, device_limit: int | None) -> int:
    """Return the traffic granted for slots above the tariff base device count."""
    if tariff is None:
        return 0

    traffic_per_device = max(0, int(getattr(tariff, 'device_traffic_gb', 0) or 0))
    base_devices = max(1, int(getattr(tariff, 'device_limit', 1) or 1))
    current_devices = max(base_devices, int(device_limit or base_devices))
    return max(0, current_devices - base_devices) * traffic_per_device


def apply_device_traffic_bonus(subscription: Subscription, tariff: Tariff | None) -> int:
    """Replace only the device bonus component and return its delta in GB."""
    total_traffic = max(0, int(subscription.traffic_limit_gb or 0))
    old_bonus = max(0, int(getattr(subscription, 'device_bonus_traffic_gb', 0) or 0))

    if total_traffic <= 0 or tariff is None:
        new_bonus = 0
    else:
        new_bonus = calculate_device_traffic_bonus(tariff, subscription.device_limit)

    subscription.device_bonus_traffic_gb = new_bonus
    if total_traffic > 0:
        subscription.traffic_limit_gb = max(0, total_traffic - min(old_bonus, total_traffic) + new_bonus)

    return new_bonus - old_bonus


def rebuild_traffic_with_device_bonus(
    subscription: Subscription,
    tariff: Tariff | None,
    base_traffic_limit_gb: int,
    *,
    preserve_purchased_traffic: bool = True,
) -> int:
    """Rebuild the effective limit from base, temporary purchases and device bonus."""
    base_traffic = max(0, int(base_traffic_limit_gb or 0))
    purchased_traffic = (
        max(0, int(subscription.purchased_traffic_gb or 0)) if preserve_purchased_traffic else 0
    )
    bonus = calculate_device_traffic_bonus(tariff, subscription.device_limit) if base_traffic > 0 else 0

    subscription.device_bonus_traffic_gb = bonus
    subscription.traffic_limit_gb = 0 if base_traffic <= 0 else base_traffic + purchased_traffic + bonus
    return subscription.traffic_limit_gb


async def sync_device_traffic_bonus(
    db: AsyncSession,
    subscription: Subscription,
    tariff: Tariff | None = None,
) -> int:
    """Load the subscription tariff if needed and synchronize its device traffic bonus."""
    if tariff is None and subscription.tariff_id:
        tariff = await db.get(Tariff, subscription.tariff_id)
    return apply_device_traffic_bonus(subscription, tariff)
