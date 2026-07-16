from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import Subscription, User
from app.services.metered_traffic_policy import get_customer_squad_uuids, preserve_metered_squad
from app.utils.pricing_utils import calculate_prorated_price, get_remaining_months

from .common import get_addon_discount_percent_for_user, get_period_hint_from_subscription
from .settings import prepare_server_catalog


def resolve_selected_server_order(payload) -> list[str]:
    raw_selection: list[str] = []
    for collection in (
        payload.servers,
        payload.squads,
        payload.server_uuids,
        payload.squad_uuids,
    ):
        if collection:
            raw_selection.extend(collection)

    selected_order: list[str] = []
    seen: set[str] = set()
    for item in raw_selection:
        if not item:
            continue
        uuid = str(item).strip()
        if not uuid or uuid in seen:
            continue
        seen.add(uuid)
        selected_order.append(uuid)

    if not selected_order:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'validation_error',
                'message': 'At least one server must be selected',
            },
        )

    return selected_order


def resolve_server_changes(
    subscription: Subscription, selected_order: list[str]
) -> tuple[list[str], list[str], list[str]]:
    current_squads = get_customer_squad_uuids(subscription.connected_squads)
    current_set = set(current_squads)
    selected_set = set(selected_order)

    added = [uuid for uuid in selected_order if uuid not in current_set]
    removed = [uuid for uuid in current_squads if uuid not in selected_set]
    return current_squads, added, removed


async def build_servers_update_plan(
    db: AsyncSession,
    user: User,
    subscription: Subscription,
    *,
    selected_order: list[str],
    added: list[str],
    removed: list[str],
) -> dict[str, Any]:
    period_hint_days = get_period_hint_from_subscription(subscription)
    servers_discount = get_addon_discount_percent_for_user(user, 'servers', period_hint_days)
    _, _, catalog = await prepare_server_catalog(
        db,
        user,
        subscription,
        servers_discount,
    )

    invalid_servers = [uuid for uuid in selected_order if uuid not in catalog]
    if invalid_servers:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'invalid_servers',
                'message': 'Some of the selected servers are not available',
            },
        )

    for uuid in added:
        entry = catalog.get(uuid)
        if not entry or not entry.get('available_for_new', False):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={
                    'code': 'server_unavailable',
                    'message': 'Selected server is not available',
                },
            )

    cost_per_month = sum(int(catalog[uuid].get('discounted_per_month', 0)) for uuid in added)
    if cost_per_month > 0:
        total_cost, charged_months = calculate_prorated_price(
            cost_per_month,
            subscription.end_date,
        )
    else:
        total_cost = 0
        charged_months = get_remaining_months(subscription.end_date)

    added_server_ids = [catalog[uuid].get('server_id') for uuid in added if catalog[uuid].get('server_id') is not None]
    added_server_prices = [
        int(catalog[uuid].get('discounted_per_month', 0)) * charged_months
        for uuid in added
        if catalog[uuid].get('server_id') is not None
    ]
    removed_server_ids = [
        catalog[uuid].get('server_id') for uuid in removed if catalog[uuid].get('server_id') is not None
    ]

    return {
        'catalog': catalog,
        'total_cost': int(total_cost),
        'charged_months': int(charged_months),
        'added_server_ids': added_server_ids,
        'added_server_prices': added_server_prices,
        'removed_server_ids': removed_server_ids,
    }


async def apply_servers_update_plan(
    db: AsyncSession,
    user: User,
    subscription: Subscription,
    *,
    selected_order: list[str],
    added: list[str],
    total_cost: int,
    charged_months: int,
    catalog: dict[str, dict[str, Any]],
    added_server_ids: list[int],
    added_server_prices: list[int],
    removed_server_ids: list[int],
    logger,
) -> None:
    from app.database.crud.server_squad import update_server_user_counts
    from app.database.crud.subscription import add_subscription_servers, remove_subscription_servers
    from app.database.crud.transaction import create_transaction
    from app.database.crud.user import subtract_user_balance
    from app.database.models import TransactionType

    if total_cost > 0 and getattr(user, 'balance_kopeks', 0) < total_cost:
        missing = total_cost - getattr(user, 'balance_kopeks', 0)
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                'code': 'insufficient_funds',
                'message': f'Недостаточно средств на балансе. Не хватает {settings.format_price(missing)}',
            },
        )

    if total_cost > 0:
        added_names = [catalog[uuid].get('name', uuid) for uuid in added]
        description = (
            f'Добавление серверов: {", ".join(added_names)} на {charged_months} мес'
            if added_names
            else 'Изменение списка серверов'
        )

        success = await subtract_user_balance(
            db,
            user,
            total_cost,
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
            amount_kopeks=total_cost,
            description=description,
        )

    if added_server_ids:
        await add_subscription_servers(db, subscription, added_server_ids, added_server_prices)

    if removed_server_ids:
        await remove_subscription_servers(db, subscription.id, removed_server_ids)

    if added_server_ids or removed_server_ids:
        try:
            await update_server_user_counts(
                db,
                add_ids=added_server_ids or None,
                remove_ids=removed_server_ids or None,
            )
        except Exception as error:
            logger.error('Ошибка обновления счётчика серверов', e=error)

    ordered_selection = []
    seen_selection = set()
    for uuid in selected_order:
        if uuid in seen_selection:
            continue
        seen_selection.add(uuid)
        ordered_selection.append(uuid)
    subscription.connected_squads = preserve_metered_squad(
        subscription.connected_squads,
        ordered_selection,
    )
