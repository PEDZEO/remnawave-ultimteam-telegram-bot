"""Anonymous support chat endpoints for the public cabinet."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cabinet.routes.auth import _get_auth_client_ip
from app.cabinet.routes.websocket import (
    notify_admins_new_ticket,
    notify_admins_ticket_reply,
)
from app.cabinet.schemas.tickets import (
    GuestTicketCreateRequest,
    GuestTicketCreateResponse,
    TicketDetailResponse,
    TicketMessageCreateRequest,
    TicketMessageResponse,
)
from app.config import settings
from app.database.models import Ticket, TicketMessage
from app.handlers.tickets import notify_admins_about_new_ticket, notify_admins_about_ticket_reply
from app.utils.cache import RateLimitCache

from ..dependencies import get_cabinet_db


logger = structlog.get_logger(__name__)
router = APIRouter(prefix='/public/support', tags=['Cabinet Guest Support'])


def hash_guest_token(token: str) -> str:
    secret = settings.get_cabinet_jwt_secret().encode()
    return hmac.new(secret, token.encode(), hashlib.sha256).hexdigest()


def _message_response(message: TicketMessage) -> TicketMessageResponse:
    return TicketMessageResponse(
        id=message.id,
        message_text=message.message_text or '',
        is_from_admin=message.is_from_admin,
        has_media=bool(message.media_file_id),
        media_type=message.media_type,
        media_file_id=message.media_file_id,
        media_caption=message.media_caption,
        created_at=message.created_at,
    )


def _ticket_response(ticket: Ticket) -> TicketDetailResponse:
    messages = sorted(ticket.messages or [], key=lambda item: item.created_at)
    return TicketDetailResponse(
        id=ticket.id,
        title=ticket.title,
        status=ticket.status,
        priority=ticket.priority or 'normal',
        created_at=ticket.created_at,
        updated_at=ticket.updated_at or ticket.created_at,
        closed_at=ticket.closed_at,
        is_reply_blocked=ticket.is_user_reply_blocked,
        messages=[_message_response(message) for message in messages],
    )


async def _rate_limit(request: Request, action: str, *, limit: int, window: int) -> None:
    client_ip = _get_auth_client_ip(request)
    if await RateLimitCache.is_rate_limited(
        f'guest:{client_ip}',
        action,
        limit=limit,
        window=window,
        fail_closed=True,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail='Too many requests. Please try again later.',
        )


async def _get_guest_ticket(db: AsyncSession, ticket_id: int, token: str) -> Ticket:
    if len(token) < 32:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid support access token')

    result = await db.execute(
        select(Ticket)
        .where(
            Ticket.id == ticket_id,
            Ticket.user_id.is_(None),
            Ticket.guest_token_hash == hash_guest_token(token),
        )
        .options(selectinload(Ticket.messages))
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Support conversation not found')
    return ticket


@router.post('/sessions', response_model=GuestTicketCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_guest_support_session(
    payload: GuestTicketCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_cabinet_db),
):
    if not settings.is_support_tickets_enabled():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Support chat is disabled')
    await _rate_limit(request, 'guest_support_create', limit=4, window=3600)

    access_token = secrets.token_urlsafe(48)
    now = datetime.now(UTC)
    ticket = Ticket(
        user_id=None,
        guest_name=payload.name.strip(),
        guest_contact=payload.contact.strip() or None,
        guest_token_hash=hash_guest_token(access_token),
        title=payload.title.strip(),
        status='open',
        priority='normal',
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    await db.flush()
    db.add(
        TicketMessage(
            ticket_id=ticket.id,
            user_id=None,
            message_text=payload.message.strip(),
            is_from_admin=False,
            created_at=now,
        )
    )
    await db.commit()
    await db.refresh(ticket, ['messages'])

    try:
        await notify_admins_about_new_ticket(ticket, db)
    except Exception as error:
        logger.warning('Failed to send guest ticket Telegram notification', error=error)
    await notify_admins_new_ticket(ticket.id, ticket.title, 0)

    return GuestTicketCreateResponse(ticket=_ticket_response(ticket), access_token=access_token)


@router.get('/sessions/{ticket_id}', response_model=TicketDetailResponse)
async def get_guest_support_session(
    ticket_id: int,
    x_guest_token: str = Header(..., alias='X-Guest-Token'),
    db: AsyncSession = Depends(get_cabinet_db),
):
    return _ticket_response(await _get_guest_ticket(db, ticket_id, x_guest_token))


@router.post('/sessions/{ticket_id}/messages', response_model=TicketMessageResponse)
async def add_guest_support_message(
    ticket_id: int,
    payload: TicketMessageCreateRequest,
    request: Request,
    x_guest_token: str = Header(..., alias='X-Guest-Token'),
    db: AsyncSession = Depends(get_cabinet_db),
):
    await _rate_limit(request, 'guest_support_message', limit=20, window=60)
    ticket = await _get_guest_ticket(db, ticket_id, x_guest_token)
    if ticket.status == 'closed':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Support conversation is closed')
    if ticket.is_user_reply_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Replies are disabled')

    now = datetime.now(UTC)
    message_text = (payload.message or '').strip()
    if not message_text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Message is required')
    message = TicketMessage(
        ticket_id=ticket.id,
        user_id=None,
        message_text=message_text,
        is_from_admin=False,
        created_at=now,
    )
    db.add(message)
    ticket.status = 'open'
    ticket.updated_at = now
    await db.commit()
    await db.refresh(message)

    try:
        await notify_admins_about_ticket_reply(ticket, message_text, db)
    except Exception as error:
        logger.warning('Failed to send guest reply Telegram notification', error=error)
    await notify_admins_ticket_reply(ticket.id, message_text[:100], 0)
    return _message_response(message)
