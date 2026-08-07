from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.cabinet.routes.tickets import add_ticket_message
from app.cabinet.schemas.tickets import TicketMessageCreateRequest


@pytest.mark.asyncio
async def test_cabinet_rejects_reply_when_admin_has_blocked_ticket() -> None:
    ticket = SimpleNamespace(id=1, status='open', is_user_reply_blocked=True)
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: ticket)),
        commit=AsyncMock(),
    )

    with pytest.raises(HTTPException, match='Replies to this ticket are blocked') as error:
        await add_ticket_message(
            ticket_id=1,
            request=TicketMessageCreateRequest(message='Please help me'),
            user=SimpleNamespace(id=7),
            db=db,
        )

    assert error.value.status_code == 403
    db.commit.assert_not_awaited()
