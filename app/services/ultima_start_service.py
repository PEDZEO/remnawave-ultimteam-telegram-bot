from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlparse

import structlog
from aiogram import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import SystemSetting
from app.keyboards.inline import get_subscription_widget_button
from app.localization.loader import DEFAULT_LANGUAGE
from app.utils.miniapp_buttons import build_cabinet_url
from app.utils.miniapp_url import add_miniapp_cache_buster


logger = structlog.get_logger(__name__)


ULTIMA_MODE_ENABLED_KEY = 'CABINET_ULTIMA_MODE_ENABLED'
ULTIMA_START_CONFIG_KEY = 'ULTIMA_START_BOT_CONFIG'
ULTIMA_NOTIFICATION_BUTTONS_CONFIG_KEY = 'ULTIMA_NOTIFICATION_BUTTONS_CONFIG'

DEFAULT_MESSAGE_TEXT = (
    '🙌 <b>Первые 3 дня бесплатно для всех пользователей:</b>\n\n'
    '1️⃣ Откройте приложение\n'
    '2️⃣ Нажмите «Установка и настройка» и следуйте инструкции, чтобы подключить устройство\n'
    '3️⃣ Готово! Пользуйтесь VPN бесплатно 3 дня\n\n'
    'Возникли вопросы или сложности? Напишите в службу поддержки, мы обязательно вам поможем 👨🏻‍💻'
)
DEFAULT_BUTTON_TEXT = '📱 Приложение'
DEFAULT_NOTIFICATION_BUTTONS: tuple[tuple[str, str], ...] = (
    ('💳 Купить подписку', '/subscription/purchase'),
    ('💰 Пополнить баланс', '/balance/top-up'),
    ('🛠 Установка и настройка', '/connection'),
    ('💬 Поддержка', '/support'),
)
ULTIMA_NOTIFICATION_ALLOWED_PATHS: frozenset[str] = frozenset(
    {
        '/',
        '/subscription',
        '/subscription/purchase',
        '/connection',
        '/support',
        '/profile',
        '/balance/top-up',
        '/ultima/gift',
    }
)


@dataclass(slots=True)
class UltimaStartConfig:
    enabled: bool
    message_text: str
    button_text: str
    button_url: str


@dataclass(slots=True)
class UltimaNotificationButton:
    text: str
    path: str


@dataclass(slots=True)
class UltimaNotificationConfig:
    enabled: bool
    buttons: list[UltimaNotificationButton]


async def is_ultima_mode_enabled(db: AsyncSession) -> bool:
    result = await db.execute(select(SystemSetting.value).where(SystemSetting.key == ULTIMA_MODE_ENABLED_KEY))
    value = result.scalar_one_or_none()
    return str(value).strip().lower() == 'true'


async def get_ultima_start_config(db: AsyncSession) -> UltimaStartConfig:
    result = await db.execute(select(SystemSetting.value).where(SystemSetting.key == ULTIMA_START_CONFIG_KEY))
    raw = result.scalar_one_or_none()

    payload: dict[str, str] = {}
    if raw:
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                payload = loaded
        except (TypeError, json.JSONDecodeError):
            payload = {}

    enabled = _coerce_bool(payload.get('enabled'), default=True)
    message_text = str(payload.get('message_text') or DEFAULT_MESSAGE_TEXT).strip()
    button_text = str(payload.get('button_text') or DEFAULT_BUTTON_TEXT).strip()
    button_url = _normalize_button_url(payload.get('button_url'))

    return UltimaStartConfig(
        enabled=enabled,
        message_text=message_text or DEFAULT_MESSAGE_TEXT,
        button_text=button_text or DEFAULT_BUTTON_TEXT,
        button_url=button_url,
    )


async def set_ultima_start_config(
    db: AsyncSession,
    *,
    enabled: bool,
    message_text: str,
    button_text: str,
    button_url: str,
) -> UltimaStartConfig:
    config = UltimaStartConfig(
        enabled=enabled,
        message_text=message_text.strip() or DEFAULT_MESSAGE_TEXT,
        button_text=button_text.strip() or DEFAULT_BUTTON_TEXT,
        button_url=_normalize_button_url(button_url),
    )

    payload = {
        'enabled': config.enabled,
        'message_text': config.message_text,
        'button_text': config.button_text,
        'button_url': config.button_url,
    }

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == ULTIMA_START_CONFIG_KEY))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = SystemSetting(key=ULTIMA_START_CONFIG_KEY, value=json.dumps(payload, ensure_ascii=False))
        db.add(setting)
    else:
        setting.value = json.dumps(payload, ensure_ascii=False)

    await db.flush()
    return config


def build_ultima_start_keyboard(
    config: UltimaStartConfig, language: str = DEFAULT_LANGUAGE
) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=config.button_text,
                    web_app=types.WebAppInfo(url=config.button_url),
                )
            ],
            [get_subscription_widget_button(language)],
        ]
    )


def is_ultima_start_button_usable(config: UltimaStartConfig) -> bool:
    parsed = urlparse((config.button_url or '').strip())
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        return False
    if parsed.netloc.lower() == 't.me' and not parsed.path.strip('/'):
        return False
    return True


async def get_ultima_notification_config(db: AsyncSession) -> UltimaNotificationConfig:
    result = await db.execute(
        select(SystemSetting.value).where(SystemSetting.key == ULTIMA_NOTIFICATION_BUTTONS_CONFIG_KEY)
    )
    raw = result.scalar_one_or_none()

    payload: dict[str, object] = {}
    if raw:
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                payload = loaded
        except (TypeError, json.JSONDecodeError):
            payload = {}

    enabled = _coerce_bool(payload.get('enabled'), default=True)
    buttons = _normalize_notification_buttons(payload.get('buttons'))
    return UltimaNotificationConfig(enabled=enabled, buttons=buttons)


async def set_ultima_notification_config(
    db: AsyncSession,
    *,
    enabled: bool,
    buttons: list[UltimaNotificationButton],
) -> UltimaNotificationConfig:
    normalized_buttons = _normalize_notification_buttons(
        [{'text': button.text, 'path': button.path} for button in buttons]
    )
    config = UltimaNotificationConfig(enabled=enabled, buttons=normalized_buttons)

    payload = {
        'enabled': config.enabled,
        'buttons': [{'text': button.text, 'path': button.path} for button in config.buttons],
    }

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == ULTIMA_NOTIFICATION_BUTTONS_CONFIG_KEY))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = SystemSetting(
            key=ULTIMA_NOTIFICATION_BUTTONS_CONFIG_KEY, value=json.dumps(payload, ensure_ascii=False)
        )
        db.add(setting)
    else:
        setting.value = json.dumps(payload, ensure_ascii=False)

    await db.flush()
    return config


def build_ultima_notification_keyboard(config: UltimaNotificationConfig) -> types.InlineKeyboardMarkup | None:
    if not config.enabled or not config.buttons:
        return None

    rows: list[list[types.InlineKeyboardButton]] = []
    row: list[types.InlineKeyboardButton] = []
    for button in config.buttons:
        url = build_cabinet_url(button.path)
        if not url:
            logger.warning(
                'Skip Ultima notification button because MINIAPP_CUSTOM_URL is not configured',
                path=button.path,
            )
            continue
        row.append(
            types.InlineKeyboardButton(
                text=button.text,
                web_app=types.WebAppInfo(url=url),
            )
        )
        if len(row) >= 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    if not rows:
        return None

    return types.InlineKeyboardMarkup(inline_keyboard=rows)


def _normalize_notification_buttons(value: object) -> list[UltimaNotificationButton]:
    default_buttons = [UltimaNotificationButton(text=text, path=path) for text, path in DEFAULT_NOTIFICATION_BUTTONS]
    if not isinstance(value, list):
        return default_buttons

    buttons: list[UltimaNotificationButton] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue

        text = str(entry.get('text') or '').strip()
        path = _normalize_notification_path(entry.get('path'))
        if not text or not path:
            continue

        buttons.append(UltimaNotificationButton(text=text[:64], path=path))
        if len(buttons) >= 6:
            break

    return buttons or default_buttons


def _normalize_notification_path(value: object) -> str:
    path = str(value or '').strip()
    if not path:
        return ''
    if not path.startswith('/'):
        path = f'/{path}'
    if path.endswith('/') and path != '/':
        path = path[:-1]
    if path not in ULTIMA_NOTIFICATION_ALLOWED_PATHS:
        return ''
    return path


def _coerce_bool(value: object, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {'true', '1', 'yes', 'on'}:
            return True
        if normalized in {'false', '0', 'no', 'off'}:
            return False
    return default


def _normalize_button_url(value: object) -> str:
    raw = str(value or '').strip()
    if raw.startswith('http://') or raw.startswith('https://'):
        return add_miniapp_cache_buster(raw)

    miniapp_url = (settings.MINIAPP_CUSTOM_URL or '').strip()
    if miniapp_url.startswith('http://') or miniapp_url.startswith('https://'):
        return add_miniapp_cache_buster(miniapp_url)

    bot_username = (settings.BOT_USERNAME or '').strip().lstrip('@')
    if bot_username:
        return f'https://t.me/{bot_username}/app'

    return 'https://t.me'
