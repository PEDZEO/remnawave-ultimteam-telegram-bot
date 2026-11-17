import json
import zlib
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram import Dispatcher
from aiogram.types import Chat, Message, Update, User as TelegramUser

from app.handlers import subscription_widget as widget


TELEGRAM_USER = TelegramUser(id=123, is_bot=False, first_name='Test')
PRIVATE_CHAT = Chat(id=TELEGRAM_USER.id, type='private')
ACCOUNT_ID = 234
BOT_ID = 345
MESSAGE_ID = 456


def _account(subscription=None):
    return SimpleNamespace(id=ACCOUNT_ID, telegram_id=TELEGRAM_USER.id, status='active', subscription=subscription)


def _query(**overrides):
    return Update.model_validate(
        {
            'update_id': 1,
            'widget_query': {
                'id': 'widget-query-id',
                'from': TELEGRAM_USER.model_dump(),
                'chat': PRIVATE_CHAT.model_dump(),
                'chat_instance': 'instance',
                'message_id': MESSAGE_ID,
                'type': {'type': 'data'},
                'data': 'refresh:v1',
                **overrides,
            },
        }
    ).widget_query


def test_widget_fits_telegram_limits_and_enables_updates():
    source = widget._widget_html().encode()
    assert len(source) <= 32768
    assert len(zlib.compress(source, 9)) <= 4096
    dispatcher = Dispatcher()
    widget.register_handlers(dispatcher)
    assert 'widget_query' in dispatcher.resolve_used_update_types()


def test_widget_falls_back_to_safe_miniapp_url(monkeypatch):
    monkeypatch.setattr(widget.settings, 'CABINET_URL', widget.settings._CABINET_URL_DEFAULT)
    monkeypatch.setattr(widget.settings, 'MINIAPP_CUSTOM_URL', 'https://miniapp.example.test/app/?next=secret#anchor')
    assert widget._public_data()['connection'] == 'https://miniapp.example.test/app/connection'

    monkeypatch.setattr(widget.settings, 'MINIAPP_CUSTOM_URL', 'https://user:secret@miniapp.example.test/app/')
    assert 'connection' not in widget._public_data()


@pytest.mark.asyncio
async def test_sends_protected_widget_and_binds_sent_message_to_account(monkeypatch):
    monkeypatch.setattr(widget.settings, 'CABINET_URL', 'https://cabinet.example.test/?unexpected=sensitive#private')
    cache_set = AsyncMock(return_value=True)
    monkeypatch.setattr(widget.cache, 'set', cache_set)
    bot = SimpleNamespace(
        id=BOT_ID,
        send_widget=AsyncMock(return_value=SimpleNamespace(chat=PRIVATE_CHAT, message_id=MESSAGE_ID)),
    )
    message = Message(message_id=1, date=datetime.now(UTC), chat=PRIVATE_CHAT, from_user=TELEGRAM_USER)

    await widget.send_subscription_widget(message, bot, _account())

    payload = bot.send_widget.await_args.kwargs
    assert payload['chat_id'] == PRIVATE_CHAT.id
    assert payload['protect_content'] is True
    assert payload['allow_queries'] is True
    assert 'Нет подписки' in payload['caption']
    assert json.loads(payload['chat_data'])['status'] == 'Нет подписки'
    assert json.loads(payload['public_data']) == {
        'brand': widget._public_data()['brand'],
        'cabinet': 'https://cabinet.example.test/',
        'connection': 'https://cabinet.example.test/connection',
    }
    cache_set.assert_awaited_once_with(
        f'subscription_widget:v1:{BOT_ID}:{PRIVATE_CHAT.id}:{MESSAGE_ID}', ACCOUNT_ID, expire=widget._WIDGET_LIFETIME
    )


@pytest.mark.asyncio
async def test_foreign_chat_never_loads_user_or_updates_widget(monkeypatch):
    cache_get = AsyncMock()
    monkeypatch.setattr(widget.cache, 'get', cache_get)
    bot = SimpleNamespace(id=BOT_ID, edit_message_widget_data=AsyncMock(), answer_widget_query=AsyncMock())
    query = _query(chat={'id': 999, 'type': 'private'})

    await widget.refresh_subscription_widget(query, bot)

    cache_get.assert_not_awaited()
    bot.edit_message_widget_data.assert_not_awaited()
    bot.answer_widget_query.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(('status', 'used', 'remaining'), [('active', 18, 82), ('limited', 100, 0)])
async def test_refresh_updates_only_the_current_owner_snapshot(monkeypatch, status, used, remaining):
    now = datetime.now(UTC)
    subscription = SimpleNamespace(
        actual_status=status,
        tariff=SimpleNamespace(name='Обычный'),
        traffic_limit_gb=100,
        traffic_used_gb=used,
        end_date=now.replace(year=now.year + 1, day=1),
        metered_access_blocked=status == 'limited',
    )
    monkeypatch.setattr(widget, 'subscription_allows_special_servers', lambda *args, **kwargs: True)
    reset = datetime(2026, 11, 24, 12, 30, tzinfo=UTC)
    monkeypatch.setattr(widget, 'get_metered_traffic_period', lambda *args, **kwargs: (None, reset))
    monkeypatch.setattr(widget.cache, 'get', AsyncMock(return_value=ACCOUNT_ID))
    monkeypatch.setattr(widget.cache, 'setnx', AsyncMock(return_value=True))
    monkeypatch.setattr(widget.cache, 'expire', AsyncMock(return_value=True))
    monkeypatch.setattr(widget.blacklist_service, 'is_user_blacklisted', AsyncMock(return_value=(False, None)))
    monkeypatch.setattr(widget, 'AsyncSessionLocal', AsyncMock)
    load_user = AsyncMock(return_value=_account(subscription))
    monkeypatch.setattr(widget, 'get_user_by_telegram_id', load_user)
    bot = SimpleNamespace(
        id=BOT_ID,
        edit_message_widget_data=AsyncMock(),
        answer_widget_query=AsyncMock(),
        edit_message_caption=AsyncMock(),
    )

    await widget.refresh_subscription_widget(_query(), bot)

    assert load_user.await_args.args[1] == TELEGRAM_USER.id
    edited = bot.edit_message_widget_data.await_args.kwargs
    assert (edited['chat_id'], edited['message_id']) == (PRIVATE_CHAT.id, MESSAGE_ID)
    assert 'public_data' not in edited
    state = json.loads(edited['chat_data'])
    assert state['remaining'] == remaining
    assert state['reset'] == '24.11.2026, 15:30 МСК'
    assert state['special'] is True
    assert len(edited['chat_data'].encode()) <= 1024
    assert f'{remaining} из 100 ГБ' in bot.edit_message_caption.await_args.kwargs['caption']

    bot.edit_message_widget_data.reset_mock()
    load_user.return_value = SimpleNamespace(id=ACCOUNT_ID + 1, status='active')
    await widget.refresh_subscription_widget(_query(), bot)
    bot.edit_message_widget_data.assert_not_awaited()
