"""Admin settings routes for cabinet - system configuration management."""

from dataclasses import asdict
from string import Formatter
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Subscription, User
from app.services.metered_traffic_service import metered_traffic_service
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
        if key == 'ULTIMA_METERED_SQUAD_UUID' and len(parts) > 1:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Only one squad UUID is allowed')
        try:
            for part in parts:
                UUID(part)
        except ValueError as error:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Value must contain valid UUIDs') from error
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

    value = _coerce_value(key, payload.value)
    try:
        await bot_configuration_service.set_value(db, key, value)
    except ReadOnlySettingError as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    await db.commit()

    if key.startswith('ULTIMA_METERED_'):
        if metered_traffic_service.is_enabled():
            await metered_traffic_service.start()
        else:
            await metered_traffic_service.stop()

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

    try:
        await bot_configuration_service.reset_value(db, key)
    except ReadOnlySettingError as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    await db.commit()

    if key.startswith('ULTIMA_METERED_'):
        if metered_traffic_service.is_enabled():
            await metered_traffic_service.start()
        else:
            await metered_traffic_service.stop()

    logger.info('Admin reset setting', telegram_id=admin.telegram_id, key=key)
    return _serialize_definition(definition)
