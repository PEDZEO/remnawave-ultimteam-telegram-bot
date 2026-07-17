from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendPhoto
from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app.cabinet.routes import media


pytestmark = pytest.mark.asyncio


class _FakeSession:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class _RejectingBot:
    last_instance: _RejectingBot | None = None

    def __init__(self, *args, **kwargs) -> None:
        self.session = _FakeSession()
        type(self).last_instance = self

    async def send_photo(self, *, chat_id: int, photo) -> None:
        method = SendPhoto(chat_id=chat_id, photo='invalid-photo')
        raise TelegramBadRequest(method=method, message='IMAGE_PROCESS_FAILED')


async def test_upload_media_returns_client_error_when_telegram_rejects_photo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(media, 'Bot', _RejectingBot)
    monkeypatch.setattr(media, '_resolve_target_chat_id', lambda: -100123)

    upload = UploadFile(
        file=BytesIO(b'not-a-real-image'),
        filename='photo.png',
        headers=Headers({'content-type': 'image/png'}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await media.upload_media(
            request=SimpleNamespace(),
            user=SimpleNamespace(telegram_id=123),
            file=upload,
            media_type='photo',
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == 'Telegram rejected this file. Check its format, size, and dimensions.'
    assert _RejectingBot.last_instance is not None
    assert _RejectingBot.last_instance.session.closed is True
