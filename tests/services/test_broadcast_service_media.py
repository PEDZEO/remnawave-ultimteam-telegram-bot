from __future__ import annotations

import pytest

from app.services.broadcast_service import BroadcastConfig, BroadcastMediaConfig, BroadcastService


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
