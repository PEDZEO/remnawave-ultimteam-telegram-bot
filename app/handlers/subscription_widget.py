import asyncio
import json
import re
from datetime import UTC, datetime
from functools import cache as cached
from html import escape
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

import structlog
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatType, ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramNotFound
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Message,
    User as TelegramUser,
    WidgetQuery,
    WidgetQueryTypeData,
)
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database.crud.user import get_user_by_telegram_id
from app.database.database import AsyncSessionLocal
from app.database.models import Subscription, User, UserStatus
from app.keyboards.inline import SUBSCRIPTION_WIDGET_CALLBACK
from app.services.blacklist_service import blacklist_service
from app.services.metered_traffic_policy import (
    METERED_TRAFFIC_TIMEZONE,
    get_metered_traffic_period,
    subscription_allows_special_servers,
)
from app.utils.cache import cache


logger = structlog.get_logger(__name__)

_REFRESH_REQUEST = 'refresh:v1'
_REFRESH_CARD_CALLBACK = 'subscription_widget:refresh'
_WIDGET_LIFETIME = 90 * 24 * 60 * 60
_REFRESH_INTERVAL = 18
_LOCAL_TIME = ZoneInfo(METERED_TRAFFIC_TIMEZONE)
_STATUS_LABELS = {
    'active': 'Активна',
    'trial': 'Пробная',
    'expired': 'Истекла',
    'disabled': 'Отключена',
    'limited': 'Трафик исчерпан',
    'pending': 'Ожидает активации',
}


@cached
def _widget_html() -> str:
    return (Path(__file__).parent.parent / 'widgets' / 'subscription.html').read_text(encoding='utf-8')


def _aware_date(date: datetime) -> datetime:
    return date if date.tzinfo else date.replace(tzinfo=UTC)


def _timestamp(date: datetime) -> str:
    return _aware_date(date).astimezone(_LOCAL_TIME).strftime('%d.%m.%Y, %H:%M МСК')


def _label(value: str, length: int) -> str:
    return ''.join(character if character.isprintable() else ' ' for character in value[:length]).strip()


def _cabinet_url() -> str:
    for value in (settings.CABINET_URL, settings.MINIAPP_CUSTOM_URL):
        url = (value or '').strip()
        if not url or url == settings._CABINET_URL_DEFAULT:
            continue
        try:
            parts = urlsplit(url)
            if (
                parts.scheme == 'https'
                and parts.hostname
                and parts.hostname not in {'t.me', 'telegram.me', 'telegram.dog'}
                and parts.username is None
                and parts.password is None
                and '\\' not in parts.netloc
            ):
                base = urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip('/'), '', ''))
                if len(f'{base}/connection'.encode()) <= 256:
                    return base
        except ValueError:
            continue
    return ''


def _public_data() -> dict[str, str]:
    names = settings.get_miniapp_branding()['service_name']
    payload = {'brand': _label(names.get('ru') or names.get('default') or 'Ultima', 32) or 'Ultima'}
    if cabinet := _cabinet_url():
        payload['cabinet'] = f'{cabinet}/'
        payload['connection'] = f'{cabinet}/connection'
    return payload


def _chat_data(subscription: Subscription | None, *, now: datetime) -> dict[str, str | float | bool]:
    state: dict[str, str | float | bool] = {'rev': int(now.timestamp() * 1000), 'asof': _timestamp(now)}
    if not subscription:
        return {**state, 'status': 'Нет подписки', 'plan': 'Моя подписка'}

    actual_status = subscription.actual_status
    tariff = subscription.tariff
    metered = subscription_allows_special_servers(subscription, tariff=tariff)
    limit = max(0, subscription.traffic_limit_gb or 0)
    state.update(
        status=_STATUS_LABELS.get(actual_status, 'Недоступна'),
        active=actual_status in {'active', 'trial'},
        plan=(_label(tariff.name or '', 80) if tariff else '') or 'Моя подписка',
        expires=_timestamp(subscription.end_date) if subscription.end_date else '',
        traffic=(_label(settings.ULTIMA_METERED_SERVER_LABEL, 48) or 'Спецсерверы') if metered else 'Трафик',
        special=metered,
        quota=limit,
        remaining=round(max(0, limit - (subscription.traffic_used_gb or 0)), 2),
        blocked=metered and bool(subscription.metered_access_blocked),
    )
    if (
        metered
        and limit > 0
        and actual_status in {'active', 'trial', 'limited'}
        and subscription.end_date
        and _aware_date(subscription.end_date) > now
    ):
        _, next_reset = get_metered_traffic_period(subscription, now=now)
        state['reset'] = _timestamp(next_reset)
    return state


def _card_text(state: dict[str, str | float | bool]) -> str:
    lines = [f'<b>{escape(str(state["plan"]))}</b> · {escape(str(state["status"]))}']
    if state.get('expires'):
        lines.append(f'Действует до {state["expires"]}')
    if traffic := state.get('traffic'):
        quota = state['quota']
        remaining = state['remaining']
        amount = f'{remaining:g} из {quota:g} ГБ'.replace('.', ',') if quota else 'безлимитно'
        lines.extend(('', f'{escape(str(traffic))} · <b>{amount}</b>'))
    if state.get('reset'):
        lines.append(f'Пакет обновится {state["reset"]}')
    if state.get('special'):
        lines.append('Обычные серверы · безлимитно')
    return '\n'.join(lines)


def _card_keyboard(public: dict[str, str]) -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(text='Обновить', callback_data=_REFRESH_CARD_CALLBACK)]
    if cabinet := public.get('cabinet'):
        row.append(InlineKeyboardButton(text='Кабинет', url=cabinet))
    return InlineKeyboardMarkup(inline_keyboard=[row])


def _json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))


def _widget_key(bot_id: int, chat_id: int, message_id: int) -> str:
    return f'subscription_widget:v1:{bot_id}:{chat_id}:{message_id}'


def _can_view(message: Message, sender: TelegramUser | None, account: User) -> bool:
    return (
        message.chat.type == ChatType.PRIVATE
        and sender is not None
        and not sender.is_bot
        and sender.id == message.chat.id == account.telegram_id
        and account.status == UserStatus.ACTIVE.value
    )


async def _send_widget(message: Message, bot: Bot, db_user: User) -> None:
    state = _chat_data(db_user.subscription, now=datetime.now(UTC))
    public = _public_data()
    try:
        sent = await bot.send_widget(
            chat_id=message.chat.id,
            message_thread_id=message.message_thread_id,
            html=_widget_html(),
            width=320,
            chat_data=_json(state),
            public_data=_json(public),
            parse_mode=None,
            allow_queries=True,
        )
    except (TelegramBadRequest, TelegramNotFound) as error:
        reason = re.sub(r'\d{5,}', '[id]', error.message[:160])
        logger.warning(
            'Telegram rejected subscription widget',
            error_type=type(error).__name__,
            reason=reason if re.fullmatch(r'[A-Za-z0-9 :.,_()\[\]-]+', reason) else None,
        )
        await bot.send_message(
            chat_id=message.chat.id,
            message_thread_id=message.message_thread_id,
            text=_card_text(state),
            parse_mode=ParseMode.HTML,
            protect_content=True,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=_card_keyboard(public),
        )
        return

    await cache.set(_widget_key(bot.id, sent.chat.id, sent.message_id), db_user.id, expire=_WIDGET_LIFETIME)


async def send_subscription_widget(message: Message, bot: Bot, db_user: User | None = None) -> None:
    if db_user and _can_view(message, message.from_user, db_user):
        await _send_widget(message, bot, db_user)


async def open_subscription_widget(callback: CallbackQuery, bot: Bot, db_user: User | None = None) -> None:
    message = callback.message
    if not isinstance(message, Message) or not db_user or not _can_view(message, callback.from_user, db_user):
        await callback.answer('Виджет доступен в личном чате с ботом.')
        return

    await callback.answer()
    await _send_widget(message, bot, db_user)


async def refresh_subscription_card(callback: CallbackQuery, bot: Bot, db_user: User | None = None) -> None:
    message = callback.message
    if (
        not isinstance(message, Message)
        or not message.from_user
        or message.from_user.id != bot.id
        or not db_user
        or not _can_view(message, callback.from_user, db_user)
    ):
        await callback.answer('Откройте новый виджет из меню бота.')
        return

    state = _chat_data(db_user.subscription, now=datetime.now(UTC))
    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=_card_text(state),
            parse_mode=ParseMode.HTML,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=_card_keyboard(_public_data()),
        )
    except TelegramAPIError as error:
        if not isinstance(error, TelegramBadRequest) or 'message is not modified' not in error.message.lower():
            await callback.answer('Не удалось обновить. Откройте новый виджет из меню бота.')
            return

    await callback.answer('Данные обновлены.')


async def _answer(bot: Bot, query: WidgetQuery, message: str) -> None:
    try:
        async with asyncio.timeout(3):
            await bot.answer_widget_query(widget_query_id=query.id, data=_json({'message': message}))
    except (TimeoutError, TelegramAPIError):
        logger.debug('Telegram did not accept subscription widget query answer')


async def refresh_subscription_widget(query: WidgetQuery, bot: Bot) -> None:
    chat = query.chat
    sender = query.from_user
    message_id = query.message_id
    if (
        query.data != _REFRESH_REQUEST
        or not isinstance(query.type, WidgetQueryTypeData)
        or query.inline_message_id is not None
        or query.widget_id is not None
        or chat is None
        or chat.type != ChatType.PRIVATE
        or chat.id != sender.id
        or sender.is_bot
        or not message_id
    ):
        await _answer(bot, query, 'Обновление доступно в личном чате с ботом.')
        return

    key = _widget_key(bot.id, chat.id, message_id)
    try:
        async with asyncio.timeout(10):
            if (owner_id := await cache.get(key)) is None:
                await _answer(bot, query, 'Откройте новый виджет из меню бота.')
                return
            if not await cache.setnx(f'{key}:refresh', True, expire=_REFRESH_INTERVAL):
                await _answer(bot, query, 'Подождите несколько секунд и попробуйте снова.')
                return
            blocked, _ = await blacklist_service.is_user_blacklisted(sender.id, sender.username)
            if blocked:
                await _answer(bot, query, 'Обновление недоступно.')
                return
            async with AsyncSessionLocal() as db:
                user = await get_user_by_telegram_id(db, sender.id)
                if not user or user.id != owner_id or user.status != UserStatus.ACTIVE.value:
                    await _answer(bot, query, 'Обновление недоступно. Откройте новый виджет из меню бота.')
                    return
                state = _chat_data(user.subscription, now=datetime.now(UTC))
            await bot.edit_message_widget_data(chat_id=chat.id, message_id=message_id, chat_data=_json(state))
    except (TimeoutError, SQLAlchemyError, TelegramAPIError):
        logger.warning('Could not refresh subscription widget')
        await _answer(bot, query, 'Не удалось обновить. Попробуйте ещё раз.')
        return

    await _answer(bot, query, 'Данные обновлены.')
    await cache.expire(key, _WIDGET_LIFETIME)


def register_handlers(dp: Dispatcher) -> None:
    dp.message.register(send_subscription_widget, Command('widget'), F.chat.type == ChatType.PRIVATE)
    dp.callback_query.register(open_subscription_widget, F.data == SUBSCRIPTION_WIDGET_CALLBACK)
    dp.callback_query.register(refresh_subscription_card, F.data == _REFRESH_CARD_CALLBACK)
    dp.widget_query.register(refresh_subscription_widget)
