from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.cabinet.routes.guest_support import _get_guest_ticket, hash_guest_token


def test_guest_token_is_hashed_deterministically() -> None:
    token = 'guest-token-' + ('x' * 48)

    first = hash_guest_token(token)
    second = hash_guest_token(token)

    assert first == second
    assert first != token
    assert len(first) == 64


@pytest.mark.asyncio
async def test_guest_ticket_rejects_short_token_before_database_query() -> None:
    db = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await _get_guest_ticket(db, ticket_id=1, token='too-short')

    assert error.value.status_code == 401
    db.execute.assert_not_awaited()
