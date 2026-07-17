"""Admin settings routes for cabinet - system configuration management."""

from dataclasses import asdict
from datetime import UTC, datetime
from string import Formatter
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Subscription, User
from app.services.metered_traffic_policy import (
    extract_squad_uuids,
    get_metered_node_multipliers,
    normalize_metered_node_multiplier,
    serialize_metered_node_multipliers,
)
from app.services.metered_traffic_service import metered_traffic_service
from app.services.remnawave_service import remnawave_service
from app.services.system_settings_service import (
    ReadOnlySettingError,
    bot_configuration_service,
)

from ..dependencies import get_cabinet_db, require_permission


logger = structlog.get_logger(__name__)

router = APIRouter(prefix='/admin/settings', tags=['Admin Settings'])


# ============ Schemas ============


class SettingCategoryRef(BaseModel):
    """Reference to category."""

    key: str
    label: str


class SettingCategorySummary(BaseModel):
    """Category summary."""

    key: str
    label: str
    description: str = ''
    items: int


class SettingChoice(BaseModel):
    """Choice option for setting."""

    value: Any
    label: str
    description: str | None = None


class SettingHint(BaseModel):
    """Setting hints and guidance."""

    description: str = ''
    format: str = ''
    example: str = ''
    warning: str = ''


class SettingDefinition(BaseModel):
    """Full setting definition with current state."""

    key: str
    name: str
    category: SettingCategoryRef
    type: str
    is_optional: bool
    current: Any = Field(default=None)
    original: Any = Field(default=None)
    has_override: bool
    read_only: bool = Field(default=False)
    choices: list[SettingChoice] = Field(default_factory=list)
    hint: SettingHint | None = None


class SettingUpdateRequest(BaseModel):
    """Request to update setting value."""

    value: Any


class MeteredTrafficConfigurationUpdate(BaseModel):
    """Complete split traffic configuration managed from the admin cabinet."""

    enabled: bool
    squad_uuids: list[str] = Field(default_factory=list)
    # Kept for rolling deployments and older cabinet versions.
    squad_uuid: str = ''
    metered_node_uuids: list[str] = Field(default_factory=list)
    metered_node_multipliers: dict[str, float] = Field(default_factory=dict)
    check_interval_seconds: int = Field(ge=15, le=3600)
    warning_percent: int = Field(ge=25, le=95)
    server_label: str = Field(min_length=1, max_length=40)
    exhausted_message_ru: str = Field(min_length=1, max_length=4096)


class MeteredTrafficExhaustedUser(BaseModel):
    user_id: int
    subscription_id: int
    telegram_id: int | None = None
    username: str | None = None
    email: str | None = None
    full_name: str
    tariff_name: str | None = None
    traffic_limit_gb: int
    traffic_used_gb: float
    purchased_traffic_gb: int
    blocked_at: datetime | None = None
    last_checked_at: datetime | None = None
    subscription_end_date: datetime


class MeteredTrafficExhaustedUsersResponse(BaseModel):
    items: list[MeteredTrafficExhaustedUser]
    total: int
    page: int
    page_size: int
    pages: int


# ============ Helper Functions ============


def _coerce_value(key: str, value: Any) -> Any:
    """Convert and validate value for a setting."""
    definition = bot_configuration_service.get_definition(key)

    if value is None:
        if definition.is_optional:
            return None
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Value is required')

    python_type = definition.python_type
    normalized: Any

    try:
        if python_type is bool:
            if isinstance(value, bool):
                normalized = value
            elif isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {'true', '1', 'yes', 'on', 'да'}:
                    normalized = True
                elif lowered in {'false', '0', 'no', 'off', 'нет'}:
                    normalized = False
                else:
                    raise ValueError('invalid bool')
            else:
                raise ValueError('invalid bool')

        elif python_type is int:
            normalized = int(value)
        elif python_type is float:
            normalized = float(value)
        else:
            normalized = str(value)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Invalid value type') from None

    choices = bot_configuration_service.get_choice_options(key)
    if choices:
        allowed_values = {option.value for option in choices}
        if normalized not in allowed_values:
            readable = ', '.join(bot_configuration_service.format_value(opt.value) for opt in choices)
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Value must be one of: {readable}',
            )

    if key == 'ULTIMA_TRAFFIC_WARNING_DEFAULT_PERCENT' and not 25 <= normalized <= 95:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Traffic warning percent must be between 25 and 95')

    if key == 'ULTIMA_METERED_CHECK_INTERVAL_SECONDS' and not 15 <= normalized <= 3600:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Interval must be between 15 and 3600 seconds')

    if key == 'ULTIMA_METERED_WARNING_PERCENT' and not 25 <= normalized <= 95:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Warning percent must be between 25 and 95')

    if key == 'ULTIMA_METERED_SERVER_LABEL':
        normalized = str(normalized).strip()
        if not normalized or len(normalized) > 40:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Server label must contain 1 to 40 characters')

    if key in {'ULTIMA_METERED_SQUAD_UUID', 'ULTIMA_METERED_NODE_UUIDS'}:
        parts = [part.strip() for part in str(normalized).split(',') if part.strip()]
        try:
            for part in parts:
                UUID(part)
        except ValueError as error:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Value must contain valid UUIDs') from error
        normalized = ','.join(dict.fromkeys(parts))
        normalized = ','.join(dict.fromkeys(parts))

    if key in {'ULTIMA_TRAFFIC_WARNING_MESSAGE_RU', 'ULTIMA_METERED_EXHAUSTED_MESSAGE_RU'}:
        message = str(normalized).strip()
        if not message:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Traffic warning message cannot be empty')
        if len(message) > 4096:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Traffic warning message is too long')

        allowed_fields = {'percent', 'used_gb', 'limit_gb', 'remaining_gb'}
        try:
            parsed_fields: set[str] = set()
            for _, field_name, format_spec, conversion in Formatter().parse(message):
                if field_name is None:
                    continue
                if format_spec or conversion:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        'Traffic warning variables cannot use formatting modifiers',
                    )
                parsed_fields.add(field_name)
        except ValueError as error:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Traffic warning message has invalid braces') from error

        if parsed_fields - allowed_fields:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Traffic warning message has unsupported variables')
        normalized = message

    return normalized


async def _metered_status_payload(db: AsyncSession) -> dict[str, Any]:
    blocked = await db.scalar(select(func.count()).select_from(Subscription).where(Subscription.metered_access_blocked))
    initialized = await db.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.metered_traffic_initialized_at.is_not(None))
    )
    active = await db.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.status.in_(['active', 'trial']))
    )
    return {
        **metered_traffic_service.get_status(),
        'subscriptions': {
            'active': int(active or 0),
            'initialized': int(initialized or 0),
            'blocked': int(blocked or 0),
        },
    }


async def _load_metered_topology() -> tuple[list[Any], list[Any]]:
    """Load live internal squads and nodes from Remnawave."""
    if not remnawave_service.is_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            remnawave_service.configuration_error or 'Remnawave API is not configured',
        )

    try:
        async with remnawave_service.get_api_client() as api:
            squads = await api.get_internal_squads()
            nodes = await api.get_all_nodes()
    except Exception as error:
        logger.error('Failed to load Remnawave split traffic topology', error=error)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            'Не удалось загрузить сквады и ноды из Remnawave',
        ) from error

    return squads, nodes


async def _restore_node_multipliers(nodes: list[Any]) -> None:
    groups: dict[float, list[str]] = {}
    for node in nodes:
        multiplier = float(node.consumption_multiplier or 0)
        groups.setdefault(multiplier, []).append(node.uuid)

    async with remnawave_service.get_api_client() as api:
        for multiplier, node_uuids in groups.items():
            if node_uuids and not await api.update_nodes_consumption_multiplier(node_uuids, multiplier):
                raise RuntimeError(f'Remnawave rejected rollback to multiplier {multiplier:g}')


def _normalize_uuid_list(values: list[str], *, field_name: str) -> list[str]:
    normalized: list[str] = []
    try:
        for raw_value in values:
            stripped = str(raw_value).strip()
            if not stripped:
                continue
            value = str(UUID(stripped))
            if value not in normalized:
                normalized.append(value)
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f'{field_name} содержит некорректный UUID') from error
    return normalized


def _normalize_metered_squad_selection(payload: MeteredTrafficConfigurationUpdate) -> list[str]:
    raw_squad_uuids = (
        payload.squad_uuids
        if 'squad_uuids' in payload.model_fields_set
        else ([payload.squad_uuid] if payload.squad_uuid.strip() else [])
    )
    return _normalize_uuid_list(raw_squad_uuids, field_name='Список тарифицируемых сквадов')


async def _remove_retired_metered_squads(db: AsyncSession, retired_squad_uuids: set[str]) -> int:
    """Remove squads that stopped being technical from stored subscriptions."""
    if not retired_squad_uuids:
        return 0

    subscriptions = (await db.execute(select(Subscription))).scalars().all()
    updated = 0
    for subscription in subscriptions:
        current = extract_squad_uuids(subscription.connected_squads)
        desired = [squad_uuid for squad_uuid in current if squad_uuid not in retired_squad_uuids]
        if desired != current:
            subscription.connected_squads = desired
            updated += 1
    return updated


def _normalize_metered_node_multipliers(
    node_uuids: list[str],
    raw_values: dict[str, float],
) -> dict[str, float]:
    normalized_values: dict[str, float] = {}
    try:
        for raw_uuid, raw_multiplier in raw_values.items():
            normalized_values[str(UUID(str(raw_uuid).strip()))] = normalize_metered_node_multiplier(raw_multiplier)
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            'Коэффициент ноды должен быть от 0.1 до 100 с точностью до одного знака',
        ) from error

    unknown_nodes = set(normalized_values) - set(node_uuids)
    if unknown_nodes:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f'Коэффициенты переданы для невыбранных нод: {", ".join(sorted(unknown_nodes))}',
        )

    return {node_uuid: normalized_values.get(node_uuid, 1.0) for node_uuid in node_uuids}


def _serialize_metered_squad(squad: Any) -> dict[str, Any]:
    return {
        'uuid': squad.uuid,
        'name': squad.name,
        'members_count': int(squad.members_count or 0),
        'inbounds_count': int(squad.inbounds_count or 0),
    }


def _serialize_exhausted_subscription(subscription: Subscription) -> MeteredTrafficExhaustedUser:
    user = subscription.user
    tariff = subscription.tariff
    return MeteredTrafficExhaustedUser(
        user_id=user.id,
        subscription_id=subscription.id,
        telegram_id=user.telegram_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        tariff_name=tariff.name if tariff else None,
        traffic_limit_gb=max(0, int(subscription.traffic_limit_gb or 0)),
        traffic_used_gb=max(0.0, float(subscription.traffic_used_gb or 0.0)),
        purchased_traffic_gb=max(0, int(subscription.purchased_traffic_gb or 0)),
        blocked_at=subscription.metered_access_blocked_at,
        last_checked_at=subscription.metered_traffic_last_checked_at,
        subscription_end_date=subscription.end_date,
    )


def _serialize_metered_node(node: Any) -> dict[str, Any]:
    return {
        'uuid': node.uuid,
        'name': node.name,
        'address': node.address,
        'country_code': node.country_code,
        'is_connected': bool(node.is_connected),
        'is_disabled': bool(node.is_disabled),
        'consumption_multiplier': float(node.consumption_multiplier or 0),
    }


async def _metered_configuration_payload(
    db: AsyncSession,
    *,
    topology: tuple[list[Any], list[Any]] | None = None,
    nodes_updated: int = 0,
) -> dict[str, Any]:
    squads, nodes = topology or await _load_metered_topology()
    configured_nodes = _normalize_uuid_list(
        str(bot_configuration_service.get_current_value('ULTIMA_METERED_NODE_UUIDS') or '').split(','),
        field_name='Список нод',
    )
    configured_squads = _normalize_uuid_list(
        str(bot_configuration_service.get_current_value('ULTIMA_METERED_SQUAD_UUID') or '').split(','),
        field_name='Список сквадов',
    )
    configured_multipliers = get_metered_node_multipliers()
    topology_errors = []
    for node in nodes:
        expected = configured_multipliers.get(node.uuid, 0.0)
        actual = float(node.consumption_multiplier or 0)
        if abs(actual - expected) > 0.001:
            topology_errors.append(f'{node.name}: сейчас {actual:g}×, требуется {expected:g}×')

    return {
        'configuration': {
            'enabled': bool(bot_configuration_service.get_current_value('ULTIMA_METERED_TRAFFIC_ENABLED')),
            'squad_uuids': configured_squads,
            'squad_uuid': configured_squads[0] if configured_squads else '',
            'metered_node_uuids': configured_nodes,
            'metered_node_multipliers': configured_multipliers,
            'check_interval_seconds': int(
                bot_configuration_service.get_current_value('ULTIMA_METERED_CHECK_INTERVAL_SECONDS') or 60
            ),
            'warning_percent': int(bot_configuration_service.get_current_value('ULTIMA_METERED_WARNING_PERCENT') or 80),
            'server_label': str(
                bot_configuration_service.get_current_value('ULTIMA_METERED_SERVER_LABEL') or 'Спецсерверы'
            ),
            'exhausted_message_ru': str(
                bot_configuration_service.get_current_value('ULTIMA_METERED_EXHAUSTED_MESSAGE_RU') or ''
            ),
        },
        'status': await _metered_status_payload(db),
        'squads': sorted((_serialize_metered_squad(squad) for squad in squads), key=lambda item: item['name'].lower()),
        'nodes': sorted((_serialize_metered_node(node) for node in nodes), key=lambda item: item['name'].lower()),
        'topology_errors': topology_errors,
        'nodes_updated': nodes_updated,
    }


def _serialize_definition(definition, include_choices: bool = True) -> SettingDefinition:
    """Serialize setting definition to response model."""
    current = bot_configuration_service.get_current_value(definition.key)
    original = bot_configuration_service.get_original_value(definition.key)
    has_override = bot_configuration_service.has_override(definition.key)

    choices: list[SettingChoice] = []
    if include_choices:
        choices = [
            SettingChoice(
                value=option.value,
                label=option.label,
                description=option.description,
            )
            for option in bot_configuration_service.get_choice_options(definition.key)
        ]

    # Get setting hints
    guidance = bot_configuration_service.get_setting_guidance(definition.key)
    hint = SettingHint(
        description=guidance.get('description', ''),
        format=guidance.get('format', ''),
        example=guidance.get('example', ''),
        warning=guidance.get('warning', ''),
    )

    return SettingDefinition(
        key=definition.key,
        name=definition.display_name,
        category=SettingCategoryRef(
            key=definition.category_key,
            label=definition.category_label,
        ),
        type=definition.type_label,
        is_optional=definition.is_optional,
        current=current,
        original=original,
        has_override=has_override,
        read_only=bot_configuration_service.is_read_only(definition.key),
        choices=choices,
        hint=hint,
    )


# ============ Routes ============


@router.get('/categories', response_model=list[SettingCategorySummary])
async def list_categories(
    admin: User = Depends(require_permission('settings:read')),
):
    """Get list of setting categories."""
    categories = bot_configuration_service.get_categories()
    return [
        SettingCategorySummary(
            key=key,
            label=label,
            description=bot_configuration_service.get_category_description(key),
            items=count,
        )
        for key, label, count in categories
    ]


@router.get('', response_model=list[SettingDefinition])
async def list_settings(
    admin: User = Depends(require_permission('settings:read')),
    category: str | None = Query(default=None, alias='category_key'),
):
    """Get list of all settings or settings for a specific category."""
    items: list[SettingDefinition] = []

    if category:
        definitions = bot_configuration_service.get_settings_for_category(category)
        items.extend(_serialize_definition(defn) for defn in definitions)
        return items

    for category_key, _, _ in bot_configuration_service.get_categories():
        definitions = bot_configuration_service.get_settings_for_category(category_key)
        items.extend(_serialize_definition(defn) for defn in definitions)

    return items


@router.get('/metered-traffic/status')
async def get_metered_traffic_status(
    admin: User = Depends(require_permission('settings:read')),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Return runtime state and subscription counters for split traffic mode."""
    return await _metered_status_payload(db)


@router.get('/metered-traffic/exhausted-users', response_model=MeteredTrafficExhaustedUsersResponse)
async def get_metered_traffic_exhausted_users(
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: User = Depends(require_permission('users:read')),
    db: AsyncSession = Depends(get_cabinet_db),
) -> MeteredTrafficExhaustedUsersResponse:
    """Return active subscriptions that lost access to metered special servers."""
    filters = [
        Subscription.metered_access_blocked.is_(True),
        Subscription.status.in_(['active', 'trial']),
        Subscription.end_date > datetime.now(UTC),
        User.status == 'active',
    ]
    normalized_search = (search or '').strip()
    if normalized_search:
        pattern = f'%{normalized_search}%'
        filters.append(
            or_(
                User.username.ilike(pattern),
                User.email.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                cast(User.telegram_id, String).ilike(pattern),
            )
        )

    total = int(
        await db.scalar(select(func.count(Subscription.id)).join(User, User.id == Subscription.user_id).where(*filters))
        or 0
    )
    pages = max(1, (total + page_size - 1) // page_size)
    safe_page = min(page, pages)

    result = await db.execute(
        select(Subscription)
        .join(User, User.id == Subscription.user_id)
        .options(selectinload(Subscription.user), selectinload(Subscription.tariff))
        .where(*filters)
        .order_by(Subscription.metered_access_blocked_at.desc().nullslast(), Subscription.id.desc())
        .offset((safe_page - 1) * page_size)
        .limit(page_size)
    )
    items = [_serialize_exhausted_subscription(subscription) for subscription in result.scalars().all()]
    return MeteredTrafficExhaustedUsersResponse(
        items=items,
        total=total,
        page=safe_page,
        page_size=page_size,
        pages=pages,
    )


@router.get('/metered-traffic/configuration')
async def get_metered_traffic_configuration(
    admin: User = Depends(require_permission('settings:read')),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Return editable split traffic settings with live Remnawave topology."""
    return await _metered_configuration_payload(db)


@router.put('/metered-traffic/configuration')
async def update_metered_traffic_configuration(
    payload: MeteredTrafficConfigurationUpdate,
    admin: User = Depends(require_permission('settings:edit')),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Validate and apply split traffic settings and node multipliers together."""
    squads, nodes = await _load_metered_topology()

    squad_uuids = _normalize_metered_squad_selection(payload)
    previous_squad_uuids = _normalize_uuid_list(
        str(bot_configuration_service.get_current_value('ULTIMA_METERED_SQUAD_UUID') or '').split(','),
        field_name='Текущий список тарифицируемых сквадов',
    )
    retired_squad_uuids = set(previous_squad_uuids) - set(squad_uuids)

    node_uuids = _normalize_uuid_list(payload.metered_node_uuids, field_name='Список тарифицируемых нод')
    node_multipliers = _normalize_metered_node_multipliers(node_uuids, payload.metered_node_multipliers)
    available_squads = {squad.uuid for squad in squads}
    available_nodes = {node.uuid for node in nodes}

    missing_squads = set(squad_uuids) - available_squads
    if missing_squads:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f'Выбранные сквады больше не существуют: {", ".join(sorted(missing_squads))}',
        )
    missing_nodes = set(node_uuids) - available_nodes
    if missing_nodes:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f'Выбранные ноды больше не существуют: {", ".join(sorted(missing_nodes))}',
        )
    if payload.enabled and not squad_uuids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Для включения выберите хотя бы один тарифицируемый сквад')
    if payload.enabled and not node_uuids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Для включения выберите хотя бы одну тарифицируемую ноду')

    values = {
        'ULTIMA_METERED_SQUAD_UUID': ','.join(squad_uuids),
        'ULTIMA_METERED_NODE_UUIDS': ','.join(node_uuids),
        'ULTIMA_METERED_NODE_MULTIPLIERS': serialize_metered_node_multipliers(node_multipliers),
        'ULTIMA_METERED_CHECK_INTERVAL_SECONDS': payload.check_interval_seconds,
        'ULTIMA_METERED_WARNING_PERCENT': payload.warning_percent,
        'ULTIMA_METERED_SERVER_LABEL': payload.server_label,
        'ULTIMA_METERED_EXHAUSTED_MESSAGE_RU': payload.exhausted_message_ru,
        'ULTIMA_METERED_TRAFFIC_ENABLED': payload.enabled,
    }
    coerced_values = {key: _coerce_value(key, value) for key, value in values.items()}

    target_multipliers = {node.uuid: node_multipliers.get(node.uuid, 0.0) for node in nodes}
    multiplier_updates: dict[float, list[str]] = {}
    for node in nodes:
        target_multiplier = target_multipliers[node.uuid]
        if abs(float(node.consumption_multiplier or 0) - target_multiplier) > 0.001:
            multiplier_updates.setdefault(target_multiplier, []).append(node.uuid)

    changed_node_uuids = {node_uuid for node_uuids in multiplier_updates.values() for node_uuid in node_uuids}
    changed_nodes = [node for node in nodes if node.uuid in changed_node_uuids]
    previous_monitor_enabled = metered_traffic_service.is_enabled()
    previous_settings = {
        key: (bot_configuration_service.has_override(key), bot_configuration_service.get_current_value(key))
        for key in coerced_values
    }
    settings_mutated = False

    await metered_traffic_service.stop()
    try:
        async with remnawave_service.get_api_client() as api:
            for multiplier, update_node_uuids in sorted(
                multiplier_updates.items(),
                key=lambda item: (item[0] == 0, item[0]),
            ):
                if not await api.update_nodes_consumption_multiplier(update_node_uuids, multiplier):
                    raise RuntimeError(f'Remnawave rejected node multiplier update to {multiplier:g}')

        for key, value in coerced_values.items():
            await bot_configuration_service.set_value(db, key, value)
            settings_mutated = True
        retired_squads_removed = await _remove_retired_metered_squads(db, retired_squad_uuids)
        await db.commit()
    except Exception as error:
        await db.rollback()
        if changed_nodes:
            try:
                await _restore_node_multipliers(changed_nodes)
            except Exception as rollback_error:
                logger.error('Failed to restore Remnawave node multipliers', error=rollback_error)

        if settings_mutated:
            try:
                for key, (had_override, previous_value) in previous_settings.items():
                    if had_override:
                        await bot_configuration_service.set_value(db, key, previous_value)
                    else:
                        await bot_configuration_service.reset_value(db, key)
                await db.commit()
            except Exception as rollback_error:
                await db.rollback()
                logger.error('Failed to restore split traffic settings', error=rollback_error)

        if previous_monitor_enabled:
            try:
                await metered_traffic_service.start()
            except Exception as restart_error:
                logger.error('Failed to restart split traffic monitor after rollback', error=restart_error)

        logger.error(
            'Failed to update split traffic configuration',
            telegram_id=admin.telegram_id,
            error=error,
        )
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            'Не удалось применить конфигурацию раздельного трафика',
        ) from error

    for node in nodes:
        node.consumption_multiplier = target_multipliers[node.uuid]

    if metered_traffic_service.is_enabled():
        await metered_traffic_service.start()

    nodes_updated = len(changed_node_uuids)
    logger.info(
        'Admin updated split traffic configuration',
        telegram_id=admin.telegram_id,
        enabled=payload.enabled,
        squad_uuids=squad_uuids,
        retired_squads_removed=retired_squads_removed,
        metered_nodes=len(node_uuids),
        nodes_updated=nodes_updated,
    )
    return await _metered_configuration_payload(
        db,
        topology=(squads, nodes),
        nodes_updated=nodes_updated,
    )


@router.post('/metered-traffic/run')
async def run_metered_traffic_check(
    admin: User = Depends(require_permission('settings:edit')),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Run one reconciliation pass without waiting for the scheduler."""
    stats = await metered_traffic_service.run_once()
    logger.info('Admin started metered traffic reconciliation', telegram_id=admin.telegram_id)
    return {'run': asdict(stats), **(await _metered_status_payload(db))}


@router.get('/{key}', response_model=SettingDefinition)
async def get_setting(
    key: str,
    admin: User = Depends(require_permission('settings:read')),
):
    """Get a specific setting by key."""
    try:
        definition = bot_configuration_service.get_definition(key)
    except KeyError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Setting not found') from error

    return _serialize_definition(definition)


@router.put('/{key}', response_model=SettingDefinition)
async def update_setting(
    key: str,
    payload: SettingUpdateRequest,
    admin: User = Depends(require_permission('settings:edit')),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Update a setting value."""
    try:
        definition = bot_configuration_service.get_definition(key)
    except KeyError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Setting not found') from error

    if key.startswith('ULTIMA_METERED_'):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            'Use the split traffic configuration endpoint for metered settings',
        )

    value = _coerce_value(key, payload.value)
    try:
        await bot_configuration_service.set_value(db, key, value)
    except ReadOnlySettingError as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    await db.commit()

    logger.info('Admin updated setting to', telegram_id=admin.telegram_id, key=key, value=value)
    return _serialize_definition(definition)


@router.delete('/{key}', response_model=SettingDefinition)
async def reset_setting(
    key: str,
    admin: User = Depends(require_permission('settings:edit')),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Reset a setting to its default value."""
    try:
        definition = bot_configuration_service.get_definition(key)
    except KeyError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Setting not found') from error

    if key.startswith('ULTIMA_METERED_'):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            'Use the split traffic configuration endpoint for metered settings',
        )

    try:
        await bot_configuration_service.reset_value(db, key)
    except ReadOnlySettingError as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    await db.commit()

    logger.info('Admin reset setting', telegram_id=admin.telegram_id, key=key)
    return _serialize_definition(definition)
