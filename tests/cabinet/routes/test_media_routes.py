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


class _AcceptingBot:
    last_instance: _AcceptingBot | None = None

    def __init__(self, *args, **kwargs) -> None:
        self.session = _FakeSession()
        self.calls: list[tuple[str, int]] = []
        type(self).last_instance = self

    async def send_photo(self, *, chat_id: int, photo):
        self.calls.append(('photo', chat_id))
        return SimpleNamespace(photo=[SimpleNamespace(file_id='photo-file-id', file_unique_id='photo-unique-id')])

    async def send_video(self, *, chat_id: int, video):
        self.calls.append(('video', chat_id))
        return SimpleNamespace(video=SimpleNamespace(file_id='video-file-id', file_unique_id='video-unique-id'))

    async def send_document(self, *, chat_id: int, document):
        self.calls.append(('document', chat_id))
        return SimpleNamespace(
            document=SimpleNamespace(file_id='document-file-id', file_unique_id='document-unique-id')
        )


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


@pytest.mark.parametrize(
    ('media_type', 'content_type', 'expected_file_id'),
    [
        ('photo', 'image/png', 'photo-file-id'),
        ('video', 'video/mp4', 'video-file-id'),
        ('document', 'application/pdf', 'document-file-id'),
    ],
)
async def test_upload_media_uses_requested_telegram_method(
    monkeypatch: pytest.MonkeyPatch,
    media_type: str,
    content_type: str,
    expected_file_id: str,
) -> None:
    monkeypatch.setattr(media, 'Bot', _AcceptingBot)
    monkeypatch.setattr(media, '_resolve_target_chat_id', lambda: -100123)

    upload = UploadFile(
        file=BytesIO(b'valid-test-payload'),
        filename=f'attachment-{media_type}',
        headers=Headers({'content-type': content_type}),
    )
    request = SimpleNamespace(
        url_for=lambda route_name, **params: f'https://example.test/{route_name}/{params["file_id"]}'
    )

    result = await media.upload_media(
        request=request,
        user=SimpleNamespace(telegram_id=123),
        file=upload,
        media_type=media_type,
    )

    assert result.media_type == media_type
    assert result.file_id == expected_file_id
    assert _AcceptingBot.last_instance is not None
    assert _AcceptingBot.last_instance.calls == [(media_type, -100123)]
    assert _AcceptingBot.last_instance.session.closed is True
