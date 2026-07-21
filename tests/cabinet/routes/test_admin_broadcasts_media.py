from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.cabinet.routes.admin_broadcasts import TELEGRAM_CAPTION_MAX_LENGTH, _validate_media_caption
from app.cabinet.schemas.broadcasts import BroadcastMediaRequest


def test_media_caption_at_telegram_limit_is_allowed() -> None:
    media = BroadcastMediaRequest(type='photo', file_id='telegram-file-id')

    _validate_media_caption(media, 'a' * TELEGRAM_CAPTION_MAX_LENGTH)


def test_message_used_as_media_caption_cannot_exceed_telegram_limit() -> None:
    media = BroadcastMediaRequest(type='video', file_id='telegram-file-id')

    with pytest.raises(HTTPException) as exc_info:
        _validate_media_caption(media, 'a' * (TELEGRAM_CAPTION_MAX_LENGTH + 1))

    assert exc_info.value.status_code == 400
    assert str(TELEGRAM_CAPTION_MAX_LENGTH) in exc_info.value.detail


def test_explicit_media_caption_is_limited_by_schema() -> None:
    with pytest.raises(ValidationError):
        BroadcastMediaRequest(
            type='document',
            file_id='telegram-file-id',
            caption='a' * (TELEGRAM_CAPTION_MAX_LENGTH + 1),
        )


def test_explicit_caption_takes_precedence_over_message_text() -> None:
    media = SimpleNamespace(type='photo', file_id='telegram-file-id', caption='Short caption')

    _validate_media_caption(media, 'a' * (TELEGRAM_CAPTION_MAX_LENGTH + 1))
