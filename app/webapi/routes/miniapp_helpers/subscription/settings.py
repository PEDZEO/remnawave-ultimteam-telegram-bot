from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.server_squad import (
    get_available_server_squads,
    get_server_squad_by_uuid,
)
from app.database.models import Subscription, User
from app.services.metered_traffic_policy import get_customer_squad_uuids
from app.utils.pricing_utils import apply_percentage_discount, get_remaining_months
from app.webapi.schemas.miniapp import (
    MiniAppConnectedServer,
    MiniAppSubscriptionBillingContext,
    MiniAppSubscriptionCurrentSettings,
    MiniAppSubscriptionDeviceOption,
    MiniAppSubscriptionDevicesSettings,
    MiniAppSubscriptionServerOption,
    MiniAppSubscriptionServersSettings,
    MiniAppSubscriptionSettings,
    MiniAppSubscriptionTrafficOption,
    MiniAppSubscriptionTrafficSettings,
)

from .common import (
    get_addon_discount_percent_for_user,
    get_period_hint_from_subscription,
)


async def prepare_server_catalog(
    db: AsyncSession,
    user: User,
    subscription: Subscription,
    discount_percent: int,
) -> tuple[
    list[MiniAppConnectedServer],
    list[MiniAppSubscriptionServerOption],
    dict[str, dict[str, Any]],
]:
    available_servers = await get_available_server_squads(
        db,
        promo_group_id=getattr(user, 'promo_group_id', None),
    )
    available_by_uuid = {server.squad_uuid: server for server in available_servers}

    current_squads = get_customer_squad_uuids(subscription.connected_squads)
    catalog: dict[str, dict[str, Any]] = {}
    ordered_uuids: list[str] = []

    def register_server(server: Any | None, *, is_connected: bool = False) -> None:
        if server is None:
            return

        uuid = server.squad_uuid
        discounted_per_month, discount_per_month = apply_percentage_discount(
            int(getattr(server, 'price_kopeks', 0) or 0),
            discount_percent,
        )
        available_for_new = bool(getattr(server, 'is_available', True) and not server.is_full)

        entry = catalog.get(uuid)
        if entry:
            entry.update(
                {
                    'name': getattr(server, 'display_name', uuid),
                    'server_id': getattr(server, 'id', None),
                    'price_per_month': int(getattr(server, 'price_kopeks', 0) or 0),
                    'discounted_per_month': discounted_per_month,
                    'discount_per_month': discount_per_month,
                    'available_for_new': available_for_new,
                }
            )
            entry['is_connected'] = entry['is_connected'] or is_connected
            return

        catalog[uuid] = {
            'uuid': uuid,
            'name': getattr(server, 'display_name', uuid),
            'server_id': getattr(server, 'id', None),
            'price_per_month': int(getattr(server, 'price_kopeks', 0) or 0),
            'discounted_per_month': discounted_per_month,
            'discount_per_month': discount_per_month,
            'available_for_new': available_for_new,
            'is_connected': is_connected,
        }
        ordered_uuids.append(uuid)

    def register_placeholder(uuid: str, *, is_connected: bool = False) -> None:
        if uuid in catalog:
            catalog[uuid]['is_connected'] = catalog[uuid]['is_connected'] or is_connected
            return

        catalog[uuid] = {
            'uuid': uuid,
            'name': uuid,
            'server_id': None,
            'price_per_month': 0,
            'discounted_per_month': 0,
            'discount_per_month': 0,
            'available_for_new': False,
            'is_connected': is_connected,
        }
        ordered_uuids.append(uuid)

    current_set = set(current_squads)

    for uuid in current_squads:
        server = available_by_uuid.get(uuid)
        if server:
            register_server(server, is_connected=True)
            continue

        server = await get_server_squad_by_uuid(db, uuid)
        if server:
            register_server(server, is_connected=True)
        else:
            register_placeholder(uuid, is_connected=True)

    for server in available_servers:
        register_server(server, is_connected=server.squad_uuid in current_set)

    current_servers = [
        MiniAppConnectedServer(
            uuid=uuid,
            name=catalog.get(uuid, {}).get('name', uuid),
        )
        for uuid in current_squads
    ]

    server_options: list[MiniAppSubscriptionServerOption] = []
    discount_value = discount_percent if discount_percent > 0 else None

    for uuid in ordered_uuids:
        entry = catalog[uuid]
        available_for_new = bool(entry.get('available_for_new', False))
        is_connected = bool(entry.get('is_connected', False))
        option_available = available_for_new or is_connected
        server_options.append(
            MiniAppSubscriptionServerOption(
                uuid=uuid,
                name=entry.get('name', uuid),
                price_kopeks=int(entry.get('discounted_per_month', 0)),
                price_label=None,
                discount_percent=discount_value,
                is_connected=is_connected,
                is_available=option_available,
                disabled_reason=None if option_available else 'Server is not available',
            )
        )

    return current_servers, server_options, catalog


async def build_subscription_settings(
    db: AsyncSession,
    user: User,
    subscription: Subscription,
) -> MiniAppSubscriptionSettings:
    period_hint_days = get_period_hint_from_subscription(subscription)
    months_remaining = get_remaining_months(subscription.end_date)
    servers_discount = get_addon_discount_percent_for_user(
        user,
        'servers',
        period_hint_days,
    )
    traffic_discount = get_addon_discount_percent_for_user(
        user,
        'traffic',
        period_hint_days,
    )
    devices_discount = get_addon_discount_percent_for_user(
        user,
        'devices',
        period_hint_days,
    )

    current_servers, server_options, _ = await prepare_server_catalog(
        db,
        user,
        subscription,
        servers_discount,
    )

    traffic_options: list[MiniAppSubscriptionTrafficOption] = []
    if not settings.is_traffic_topup_blocked():
        for package in settings.get_traffic_packages():
            is_enabled = bool(package.get('enabled', True))
            if package.get('is_active') is False:
                is_enabled = False
            if not is_enabled:
                continue
            try:
                gb_value = int(package.get('gb'))
            except (TypeError, ValueError):
                continue

            price = int(package.get('price') or 0)
            discounted_price, _ = apply_percentage_discount(price, traffic_discount)
            traffic_options.append(
                MiniAppSubscriptionTrafficOption(
                    value=gb_value,
                    label=None,
                    price_kopeks=discounted_price,
                    price_label=None,
                    is_current=(gb_value == subscription.traffic_limit_gb),
                    is_available=True,
                    description=None,
                )
            )

    default_device_limit = max(settings.DEFAULT_DEVICE_LIMIT, 1)
    current_device_limit = int(subscription.device_limit or default_device_limit)

    max_devices_setting = settings.MAX_DEVICES_LIMIT if settings.MAX_DEVICES_LIMIT > 0 else None
    if max_devices_setting is not None:
        max_devices = max(max_devices_setting, current_device_limit, default_device_limit)
    else:
        max_devices = max(current_device_limit, default_device_limit) + 10

    discounted_single_device, _ = apply_percentage_discount(
        settings.PRICE_PER_DEVICE,
        devices_discount,
    )

    devices_options: list[MiniAppSubscriptionDeviceOption] = []
    for value in range(1, max_devices + 1):
        chargeable = max(0, value - default_device_limit)
        discounted_per_month, _ = apply_percentage_discount(
            chargeable * settings.PRICE_PER_DEVICE,
            devices_discount,
        )
        devices_options.append(
            MiniAppSubscriptionDeviceOption(
                value=value,
                label=None,
                price_kopeks=discounted_per_month,
                price_label=None,
            )
        )

    return MiniAppSubscriptionSettings(
        subscription_id=subscription.id,
        currency=(getattr(user, 'balance_currency', None) or 'RUB').upper(),
        current=MiniAppSubscriptionCurrentSettings(
            servers=current_servers,
            traffic_limit_gb=subscription.traffic_limit_gb,
            traffic_limit_label=None,
            device_limit=current_device_limit,
        ),
        servers=MiniAppSubscriptionServersSettings(
            available=server_options,
            min=1 if server_options else 0,
            max=len(server_options) if server_options else 0,
            can_update=True,
            hint=None,
        ),
        traffic=MiniAppSubscriptionTrafficSettings(
            options=traffic_options,
            can_update=not settings.is_traffic_topup_blocked(),
            current_value=subscription.traffic_limit_gb,
        ),
        devices=MiniAppSubscriptionDevicesSettings(
            options=devices_options,
            can_update=True,
            min=1,
            max=max_devices_setting or 0,
            step=1,
            current=current_device_limit,
            price_kopeks=discounted_single_device,
            price_label=None,
        ),
        billing=MiniAppSubscriptionBillingContext(
            months_remaining=max(1, months_remaining),
            period_hint_days=period_hint_days,
            renews_at=subscription.end_date,
        ),
    )
