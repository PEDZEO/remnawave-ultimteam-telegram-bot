from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from app.config import CLASSIC_PERIOD_PRICES, PERIOD_PRICES, settings
from app.database.crud.server_squad import get_server_squad_by_uuid
from app.services.metered_traffic_policy import get_customer_squad_uuids
from app.utils.pricing_utils import calculate_months_from_days
from app.utils.promo_offer import get_user_active_promo_discount_percent


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.database.models import Subscription, User


logger = structlog.get_logger()


@dataclass(frozen=True)
class RenewalPricing:
    """Immutable result of a renewal price calculation."""

    base_price: int  # kopeks
    servers_price: int  # kopeks
    traffic_price: int  # kopeks
    devices_price: int  # kopeks
    promo_group_discount: int  # kopeks deducted
    promo_offer_discount: int  # kopeks deducted
    final_total: int  # kopeks — amount to charge
    period_days: int
    is_tariff_mode: bool
    breakdown: dict[str, Any] = field(default_factory=dict)


class PricingEngine:
    """Unified pricing engine for all subscription renewal calculations."""

    @staticmethod
    def apply_discount(amount_kopeks: int, percent: int) -> int:
        """Apply percentage discount with integer arithmetic.
        Clamps percent to [0, 100]. Uses floor division."""
        percent = max(0, min(100, percent))
        discount = amount_kopeks * percent // 100
        return amount_kopeks - discount

    @staticmethod
    def apply_stacked_discounts(
        amount: int,
        group_percent: int,
        offer_percent: int,
    ) -> tuple[int, int, int]:
        """Apply promo-group discount, then promo-offer discount sequentially.
        Returns (final_amount, group_discount_value, offer_discount_value)."""
        after_group = PricingEngine.apply_discount(amount, group_percent)
        group_discount_value = amount - after_group
        after_offer = PricingEngine.apply_discount(after_group, offer_percent)
        offer_discount_value = after_group - after_offer
        return after_offer, group_discount_value, offer_discount_value

    async def _calculate_servers_price(
        self,
        country_uuids: list[str],
        db: AsyncSession,
        *,
        promo_group_id: int | None = None,
    ) -> tuple[int, list[dict]]:
        """Calculate total server price from connected squad UUIDs.

        Unlike the old implementation, ALWAYS uses real price_kopeks
        even when server is unavailable or full. Only orphaned UUIDs
        (not found in DB) get price=0.
        """
        total_price = 0
        details: list[dict] = []

        for uuid in country_uuids:
            try:
                server = await get_server_squad_by_uuid(db, uuid)
            except Exception as e:
                logger.error('Ошибка загрузки сервера', squad_uuid=uuid, error=str(e))
                details.append({'uuid': uuid, 'price': 0, 'status': 'error'})
                continue

            if server is None:
                logger.error('Сервер не найден в БД', squad_uuid=uuid)
                details.append({'uuid': uuid, 'price': 0, 'status': 'not_found'})
                continue

            price = server.price_kopeks or 0
            status = 'available'

            if not server.is_available:
                status = 'unavailable'
                logger.warning(
                    'Сервер недоступен, используем реальную цену',
                    squad_uuid=uuid,
                    price_kopeks=price,
                )
            elif server.is_full:
                status = 'full'
                logger.warning(
                    'Сервер переполнен, используем реальную цену',
                    squad_uuid=uuid,
                    price_kopeks=price,
                )
            elif promo_group_id is not None:
                allowed_ids = [pg.id for pg in (server.allowed_promo_groups or [])]
                if allowed_ids and promo_group_id not in allowed_ids:
                    status = 'not_allowed'
                    logger.warning(
                        'Сервер недоступен для промогруппы, используем реальную цену',
                        squad_uuid=uuid,
                        promo_group_id=promo_group_id,
                        price_kopeks=price,
                    )

            total_price += price
            details.append({'uuid': uuid, 'price': price, 'status': status})

        return total_price, details

    def _calculate_traffic_price(
        self,
        traffic_limit_gb: int,
        purchased_traffic_gb: int,
    ) -> int:
        """Calculate traffic price, separating base from purchased GB.
        Prevents purchased top-ups from inflating the tier lookup."""
        total_gb = traffic_limit_gb or 0
        purchased_gb = purchased_traffic_gb or 0
        base_gb = max(0, total_gb - purchased_gb)

        base_price = settings.get_traffic_price(base_gb) if base_gb > 0 else 0
        purchased_price = settings.get_traffic_price(purchased_gb) if purchased_gb > 0 else 0

        return base_price + purchased_price

    # ------------------------------------------------------------------
    # Main public method
    # ------------------------------------------------------------------

    async def calculate_renewal_price(
        self,
        db: AsyncSession,
        subscription: Subscription,
        period_days: int,
        *,
        user: User | None = None,
    ) -> RenewalPricing:
        """Calculate renewal price for a subscription.

        Routes to tariff mode (subscription has a tariff) or classic mode
        (legacy env-based pricing).  Stacked discounts (promo-group then
        promo-offer) are applied in both modes.
        """
        if subscription.tariff_id is not None and subscription.tariff is not None:
            return await self._calculate_tariff_mode(db, subscription, period_days, user=user)
        return await self._calculate_classic_mode(db, subscription, period_days, user=user)

    # ------------------------------------------------------------------
    # Tariff mode
    # ------------------------------------------------------------------

    async def _calculate_tariff_mode(
        self,
        db: AsyncSession,
        subscription: Subscription,
        period_days: int,
        *,
        user: User | None = None,
    ) -> RenewalPricing:
        """Price calculation when subscription is linked to a Tariff."""
        tariff = subscription.tariff
        period_prices: dict = tariff.period_prices or {}
        base_price = period_prices.get(str(period_days), 0)

        # Extra devices above the tariff's included limit
        device_price_per_unit = settings.PRICE_PER_DEVICE
        extra_devices = max(0, (subscription.device_limit or 0) - (tariff.device_limit or 0))
        devices_price = extra_devices * device_price_per_unit

        subtotal = base_price + devices_price

        # Resolve discounts
        group_pct = 0
        if user and getattr(user, 'promo_group', None) is not None:
            group_pct = user.promo_group.get_discount_percent('period', period_days)

        offer_pct = get_user_active_promo_discount_percent(user) if user else 0

        final_total, group_discount, offer_discount = self.apply_stacked_discounts(
            subtotal,
            group_pct,
            offer_pct,
        )

        breakdown = {
            'tariff_id': tariff.id,
            'extra_devices': extra_devices,
            'group_discount_pct': group_pct,
            'offer_discount_pct': offer_pct,
        }

        return RenewalPricing(
            base_price=base_price,
            servers_price=0,
            traffic_price=0,
            devices_price=devices_price,
            promo_group_discount=group_discount,
            promo_offer_discount=offer_discount,
            final_total=max(0, final_total),
            period_days=period_days,
            is_tariff_mode=True,
            breakdown=breakdown,
        )

    # ------------------------------------------------------------------
    # Classic mode
    # ------------------------------------------------------------------

    async def _calculate_classic_mode(
        self,
        db: AsyncSession,
        subscription: Subscription,
        period_days: int,
        *,
        user: User | None = None,
    ) -> RenewalPricing:
        """Price calculation for legacy (non-tariff) subscriptions.

        Uses CLASSIC_PERIOD_PRICES from settings, falling back to the
        global PERIOD_PRICES dict during migration.

        Per-category discounts (period, servers, traffic, devices) are
        applied separately to each component. Servers, traffic, and
        devices are monthly prices multiplied by months_in_period.
        """
        months = calculate_months_from_days(period_days)

        # --- Base period price (already includes full period) ---
        base_price_original = CLASSIC_PERIOD_PRICES.get(period_days)
        if base_price_original is None:
            base_price_original = PERIOD_PRICES.get(period_days, 0)

        # --- Per-category discount percents ---
        period_pct = 0
        servers_pct = 0
        traffic_pct = 0
        devices_pct = 0
        promo_group = None
        if user and getattr(user, 'promo_group', None) is not None:
            promo_group = user.promo_group
            period_pct = promo_group.get_discount_percent('period', period_days)
            servers_pct = promo_group.get_discount_percent('servers', period_days)
            traffic_pct = promo_group.get_discount_percent('traffic', period_days)
            devices_pct = promo_group.get_discount_percent('devices', period_days)

        offer_pct = get_user_active_promo_discount_percent(user) if user else 0

        # --- Base price with period discount ---
        base_price = self.apply_discount(base_price_original, period_pct)

        # --- Servers (monthly × months, with servers discount) ---
        connected_squads = get_customer_squad_uuids(subscription.connected_squads)
        promo_group_id = getattr(user, 'promo_group_id', None) if user else None
        servers_price_per_month, server_details = await self._calculate_servers_price(
            connected_squads,
            db,
            promo_group_id=promo_group_id,
        )
        discounted_servers_per_month = self.apply_discount(servers_price_per_month, servers_pct)
        servers_price = discounted_servers_per_month * months

        # --- Traffic (monthly × months, with traffic discount) ---
        traffic_limit_gb = subscription.traffic_limit_gb or 0
        purchased_traffic_gb = subscription.purchased_traffic_gb or 0
        device_bonus_traffic_gb = getattr(subscription, 'device_bonus_traffic_gb', 0) or 0
        non_base_traffic_gb = purchased_traffic_gb + device_bonus_traffic_gb
        traffic_price_per_month = self._calculate_traffic_price(traffic_limit_gb, non_base_traffic_gb)
        discounted_traffic_per_month = self.apply_discount(traffic_price_per_month, traffic_pct)
        traffic_price = discounted_traffic_per_month * months

        # --- Devices (monthly × months, with devices discount) ---
        default_device_limit = settings.DEFAULT_DEVICE_LIMIT
        device_price_per_unit = settings.PRICE_PER_DEVICE
        extra_devices = max(0, (subscription.device_limit or 0) - default_device_limit)
        devices_price_per_month = extra_devices * device_price_per_unit
        discounted_devices_per_month = self.apply_discount(devices_price_per_month, devices_pct)
        devices_price = discounted_devices_per_month * months

        # --- Subtotal (category discounts already applied) ---
        subtotal = base_price + servers_price + traffic_price + devices_price

        # --- Promo offer discount on entire subtotal ---
        promo_offer_discount = subtotal * offer_pct // 100 if offer_pct > 0 else 0
        final_total = subtotal - promo_offer_discount

        # Total group discount = sum of per-category discounts
        base_group_discount = base_price_original - base_price
        servers_group_discount = (servers_price_per_month - discounted_servers_per_month) * months
        traffic_group_discount = (traffic_price_per_month - discounted_traffic_per_month) * months
        devices_group_discount = (devices_price_per_month - discounted_devices_per_month) * months
        total_group_discount = (
            base_group_discount + servers_group_discount + traffic_group_discount + devices_group_discount
        )

        breakdown = {
            'months_in_period': months,
            'servers': server_details,
            'servers_individual_prices': [d['price'] * months for d in server_details],
            'server_ids': connected_squads,
            'base_traffic_gb': max(0, traffic_limit_gb - non_base_traffic_gb),
            'purchased_traffic_gb': purchased_traffic_gb,
            'device_bonus_traffic_gb': device_bonus_traffic_gb,
            'extra_devices': extra_devices,
            'group_discount_pct': {
                'period': period_pct,
                'servers': servers_pct,
                'traffic': traffic_pct,
                'devices': devices_pct,
            },
            'offer_discount_pct': offer_pct,
        }

        return RenewalPricing(
            base_price=base_price,
            servers_price=servers_price,
            traffic_price=traffic_price,
            devices_price=devices_price,
            promo_group_discount=total_group_discount,
            promo_offer_discount=promo_offer_discount,
            final_total=max(0, final_total),
            period_days=period_days,
            is_tariff_mode=False,
            breakdown=breakdown,
        )
