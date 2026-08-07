from __future__ import annotations

from types import SimpleNamespace

import pytest

import app.services.broadcast_service as broadcast_module
from app.services.broadcast_service import (
    BroadcastConfig,
    BroadcastMediaConfig,
    BroadcastService,
    EmailBroadcastService,
)


pytestmark = pytest.mark.asyncio


class _FakeBot:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def send_photo(self, **kwargs) -> None:
        self.calls.append(('photo', kwargs))

    async def send_video(self, **kwargs) -> None:
        self.calls.append(('video', kwargs))

    async def send_document(self, **kwargs) -> None:
        self.calls.append(('document', kwargs))

    async def send_message(self, **kwargs) -> None:
        self.calls.append(('message', kwargs))


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeRecipientSession:
    def __init__(self) -> None:
        self.calls = 0
        self.queries = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def execute(self, query):
        self.queries.append(query)
        self.calls += 1
        if self.calls == 1:
            return _FakeResult(
                [
                    SimpleNamespace(
                        id=10, email='first@example.com', username='first', first_name=None, last_name=None
                    ),
                    SimpleNamespace(
                        id=20, email='second@example.com', username=None, first_name='Second', last_name='User'
                    ),
                ]
            )
        return _FakeResult([])


@pytest.mark.parametrize('media_type', ['photo', 'video', 'document'])
async def test_deliver_message_sends_each_supported_media_type(media_type: str) -> None:
    service = BroadcastService()
    bot = _FakeBot()
    service.set_bot(bot)
    config = BroadcastConfig(
        target='active',
        message_text='Broadcast text',
        selected_buttons=[],
        media=BroadcastMediaConfig(type=media_type, file_id=f'{media_type}-file-id'),
    )

    await service._deliver_message(telegram_id=123, config=config, keyboard=None)

    assert len(bot.calls) == 1
    method, kwargs = bot.calls[0]
    assert method == media_type
    assert kwargs['chat_id'] == 123
    assert kwargs[media_type] == f'{media_type}-file-id'
    assert kwargs['caption'] == 'Broadcast text'
    assert kwargs['parse_mode'] == 'HTML'


async def test_email_recipients_are_streamed_with_keyset_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeRecipientSession()
    monkeypatch.setattr(broadcast_module, 'AsyncSessionLocal', lambda: session)
    service = EmailBroadcastService()

    batches = [batch async for batch in service._iter_email_recipient_batches('all_email', batch_size=2)]

    assert [[recipient.email for recipient in batch] for batch in batches] == [
        ['first@example.com', 'second@example.com']
    ]
    assert batches[0][1].user_name == 'Second User'
    assert all(query._offset_clause is None for query in session.queries)
