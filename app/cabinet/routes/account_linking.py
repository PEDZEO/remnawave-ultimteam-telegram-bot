"""Account linking routes for cabinet authentication."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import structlog
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.crud.user import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_oauth_provider,
    get_user_by_telegram_id,
    set_user_oauth_provider_id,
)
from app.database.models import CabinetRefreshToken, Ticket, TicketMessage, User, UserStatus
from app.handlers.tickets import notify_admins_about_new_ticket
from app.utils.cache import cache, cache_key

from ..auth import validate_telegram_init_data
from ..auth.jwt_handler import get_token_payload
from ..auth.oauth_providers import (
    OAuthUserInfo,
    build_vk_pkce_payload,
    consume_oauth_state,
    consume_oauth_state_any,
    generate_oauth_state,
    get_provider,
)
from ..dependencies import get_cabinet_db, get_current_cabinet_user
from ..schemas.account_linking import (
    LinkCodeConfirmRequest,
    LinkCodeCreateResponse,
    LinkCodePreviewRequest,
    LinkCodePreviewResponse,
    LinkedIdentitiesResponse,
    LinkedIdentity,
    LinkOperationResponse,
    LinkProviderAuthorizeResponse,
    LinkProviderCallbackRequest,
    ManualMergeRequest,
    ManualMergeResponse,
    ManualMergeTicketStatusResponse,
    PendingLinkResultResponse,
    TelegramRelinkStatus,
    UnlinkIdentityConfirmRequest,
    UnlinkIdentityRequestResponse,
    UnlinkIdentityResponse,
)
from ..schemas.auth import AuthResponse, TelegramAuthRequest
from ..services.account_linking import (
    LINK_CODE_TTL_SECONDS,
    LinkCodeAttemptsExceededError,
    LinkCodeConflictError,
    LinkCodeInvalidError,
    confirm_link_code,
    create_link_code,
    get_user_identity_hints,
    preview_link_code,
)
from ..services.manual_merge_ticket import (
    MANUAL_MERGE_TICKET_TITLE,
    build_manual_merge_ticket_message,
    parse_manual_merge_payload,
    parse_manual_merge_resolution,
)
from .auth import _create_auth_response, _store_refresh_token


logger = structlog.get_logger(__name__)
router = APIRouter(prefix='/auth', tags=['Cabinet Account Linking'])
_link_result_security = HTTPBearer(auto_error=False)

UNLINK_CONFIRM_TTL_SECONDS = 10 * 60
UNLINK_COOLDOWN_SECONDS = 24 * 60 * 60
TELEGRAM_RELINK_COOLDOWN_SECONDS = 30 * 24 * 60 * 60
UNLINK_OTP_LENGTH = 6
UNLINK_OTP_MAX_ATTEMPTS = 5
UNLINK_OTP_SEND_COOLDOWN_SECONDS = 60
UNLINK_OTP_SEND_WINDOW_SECONDS = 60 * 60
UNLINK_OTP_SEND_MAX_PER_WINDOW = 5
LINK_RESULT_TTL_SECONDS = 5 * 60

_UNLINK_PROVIDER_ATTRS: dict[str, str] = {
    'telegram': 'telegram_id',
    'google': 'google_id',
    'yandex': 'yandex_id',
    'discord': 'discord_id',
    'vk': 'vk_id',
}


def _unlink_request_key(token: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'request', token)


def _unlink_cooldown_key(user_id: int, provider: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'cooldown', user_id, provider)


def _unlink_otp_attempts_key(token: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'otp_attempts', token)


def _unlink_otp_send_cooldown_key(user_id: int, provider: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'otp_send_cooldown', user_id, provider)


def _unlink_otp_send_counter_key(user_id: int, provider: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'otp_send_counter', user_id, provider)


def _unlink_otp_send_block_key(user_id: int, provider: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'otp_send_block', user_id, provider)


def _telegram_relink_cooldown_key(user_id: int) -> str:
    return cache_key('cabinet', 'telegram_relink', 'cooldown', user_id)


def _telegram_unlink_marker_key(user_id: int) -> str:
    return cache_key('cabinet', 'telegram_relink', 'unlink_marker', user_id)


def _link_result_key(user_id: int) -> str:
    return cache_key('cabinet', 'link_identity', 'result', user_id)


def _unlink_otp_hash(otp_code: str) -> str:
    pepper = settings.get_cabinet_jwt_secret()
    return hashlib.sha256(f'{pepper}:unlink_otp:{otp_code}'.encode()).hexdigest()


def _generate_otp_code() -> str:
    # cryptographically secure 6-digit OTP
    value = secrets.randbelow(10**UNLINK_OTP_LENGTH)
    return f'{value:0{UNLINK_OTP_LENGTH}d}'


def _build_cooldown_payload(ttl_seconds: int) -> dict[str, str | bool]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=ttl_seconds)
    return {
        'active': True,
        'created_at': now.isoformat(),
        'expires_at': expires_at.isoformat(),
    }


def _parse_iso_datetime(raw_value: object) -> datetime | None:
    if not isinstance(raw_value, str) or not raw_value:
        return None
    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _extract_cooldown_state(
    payload: object,
    default_retry_after_seconds: int | None = None,
) -> tuple[bool, datetime | None, int | None]:
    if not isinstance(payload, dict) or not payload.get('active'):
        return False, None, None

    cooldown_until = _parse_iso_datetime(payload.get('expires_at'))
    if cooldown_until is not None:
        retry_after = max(int((cooldown_until - datetime.now(UTC)).total_seconds()), 0)
        if retry_after <= 0:
            return False, None, None
        return True, cooldown_until, retry_after

    return True, None, default_retry_after_seconds


_cached_bot: Bot | None = None


def _get_bot() -> Bot:
    global _cached_bot
    if _cached_bot is None:
        _cached_bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    return _cached_bot


async def _send_unlink_otp_to_telegram(telegram_id: int, provider: str, otp_code: str) -> None:
    bot = _get_bot()
    text = (
        '🔐 <b>Подтверждение отвязки входа</b>\n\n'
        f'Провайдер: <b>{provider}</b>\n'
        f'Код подтверждения: <code>{otp_code}</code>\n\n'
        f'Код действует {UNLINK_CONFIRM_TTL_SECONDS // 60} минут.\n'
        'Если это были не вы, ничего не подтверждайте.'
    )
    await bot.send_message(chat_id=telegram_id, text=text)


async def _get_unlink_block_reason(user: User, provider: str) -> str | None:
    attr_name = _UNLINK_PROVIDER_ATTRS.get(provider)
    if not attr_name:
        return 'provider_not_supported'

    linked_value = getattr(user, attr_name, None)
    if linked_value is None:
        return 'identity_not_linked'

    linked_count = len(get_user_identity_hints(user))
    if linked_count <= 1:
        return 'last_identity'

    if user.telegram_id is None:
        return 'telegram_required'

    cooldown_payload = await cache.get(_unlink_cooldown_key(user.id, provider))
    is_active, _, _ = _extract_cooldown_state(cooldown_payload, UNLINK_COOLDOWN_SECONDS)
    if is_active:
        return 'cooldown_active'

    return None


def _link_error_to_http(exc: Exception) -> HTTPException:
    detail = {'code': getattr(exc, 'code', 'link_code_error'), 'message': str(exc)}
    code = detail['code']
    if code == 'link_code_attempts_exceeded':
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
    if code in {
        'link_code_invalid',
        'link_code_same_account',
        'link_code_storage_error',
        'link_code_attempts_error',
        'link_code_user_not_found',
    }:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if code in {
        'manual_merge_required',
        'link_code_identity_conflict',
        'link_code_source_inactive',
        'link_code_target_inactive',
    }:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


async def _ensure_telegram_relink_allowed(target_user: User, source_user: User) -> None:
    """Guard Telegram account replacement and enforce relink cooldown."""
    if source_user.telegram_id is None:
        return

    if target_user.telegram_id is not None and target_user.telegram_id != source_user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': 'telegram_relink_requires_unlink',
                'message': 'To link another Telegram account, unlink current Telegram first',
            },
        )

    if target_user.telegram_id is None:
        cooldown_payload = await cache.get(_telegram_relink_cooldown_key(target_user.id))
        is_active, _, retry_after = _extract_cooldown_state(
            cooldown_payload,
            TELEGRAM_RELINK_COOLDOWN_SECONDS,
        )
        if is_active:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    'code': 'telegram_relink_cooldown_active',
                    'message': 'Telegram account can be changed only once per 30 days',
                    'retry_after_seconds': retry_after or TELEGRAM_RELINK_COOLDOWN_SECONDS,
                },
            )


async def _ensure_telegram_attach_allowed(
    target_user: User,
    *,
    source_telegram_id: int | None,
) -> None:
    """Guard Telegram link/relink for both merge and fresh attach flows."""
    if source_telegram_id is None:
        return

    if target_user.telegram_id is not None and target_user.telegram_id != source_telegram_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': 'telegram_relink_requires_unlink',
                'message': 'To link another Telegram account, unlink current Telegram first',
            },
        )

    if target_user.telegram_id is None:
        cooldown_payload = await cache.get(_telegram_relink_cooldown_key(target_user.id))
        is_active, _, retry_after = _extract_cooldown_state(
            cooldown_payload,
            TELEGRAM_RELINK_COOLDOWN_SECONDS,
        )
        if is_active:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    'code': 'telegram_relink_cooldown_active',
                    'message': 'Telegram account can be changed only once per 30 days',
                    'retry_after_seconds': retry_after or TELEGRAM_RELINK_COOLDOWN_SECONDS,
                },
            )


def _status_from_code(code: str | None) -> str:
    if code == 'manual_merge_required':
        return 'manual'
    if code:
        return 'error'
    return 'success'


def _extract_detail_code(detail: object) -> str | None:
    if isinstance(detail, dict):
        raw_code = detail.get('code')
        if isinstance(raw_code, str) and raw_code:
            return raw_code
    return None


def _extract_detail_message(detail: object, fallback: str) -> str:
    if isinstance(detail, dict):
        raw_message = detail.get('message')
        if isinstance(raw_message, str) and raw_message:
            return raw_message
    if isinstance(detail, str) and detail:
        return detail
    return fallback


def _get_link_result_user_id(credentials: HTTPAuthorizationCredentials | None) -> int:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authentication required',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    payload = get_token_payload(credentials.credentials, expected_type='access')
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    try:
        return int(payload.get('sub'))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token payload',
            headers={'WWW-Authenticate': 'Bearer'},
        ) from exc


async def _store_link_result(
    *,
    user_id: int,
    provider: str,
    status_value: str,
    message: str,
    code: str | None = None,
    auth_response: AuthResponse | None = None,
) -> None:
    payload: dict[str, object] = {
        'status': status_value,
        'provider': provider,
        'message': message,
        'code': code,
    }
    if auth_response is not None:
        payload['auth_response'] = auth_response.model_dump(mode='json')
    await cache.set(
        _link_result_key(user_id),
        payload,
        expire=LINK_RESULT_TTL_SECONDS,
    )


async def _finalize_link_auth_response(
    db: AsyncSession,
    *,
    user: User,
    provider: str,
) -> AuthResponse:
    user.cabinet_last_login = datetime.now(UTC).replace(tzinfo=None)
    await db.commit()
    auth_response = await _create_auth_response(user, db)
    await _store_refresh_token(db, user.id, auth_response.refresh_token, device_info=f'account-link:{provider}')
    return auth_response


def _fill_missing_profile_fields_from_oauth(user: User, user_info: OAuthUserInfo) -> bool:
    updated = False
    if not user.first_name and user_info.first_name:
        user.first_name = user_info.first_name
        updated = True
    if not user.last_name and user_info.last_name:
        user.last_name = user_info.last_name
        updated = True
    if not user.username and user_info.username:
        user.username = user_info.username
        updated = True
    if not user.email and user_info.email and user_info.email_verified:
        user.email = user_info.email
        user.email_verified = True
        user.email_verified_at = datetime.now(UTC).replace(tzinfo=None)
        updated = True
    if updated:
        user.updated_at = datetime.now(UTC).replace(tzinfo=None)
    return updated


async def _consume_link_oauth_state(
    *,
    state: str,
    provider: str | None = None,
) -> tuple[str, dict[str, object], int]:
    if provider:
        state_payload_raw = await consume_oauth_state(state, provider)
        resolved_provider = provider
    else:
        state_payload_raw = await consume_oauth_state_any(state)
        resolved_provider = ''
        if isinstance(state_payload_raw, dict):
            raw_provider = state_payload_raw.get('provider')
            if isinstance(raw_provider, str):
                resolved_provider = raw_provider.strip().lower()

    if not isinstance(state_payload_raw, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'oauth_state_invalid', 'message': 'Invalid or expired OAuth state'},
        )

    if state_payload_raw.get('intent') != 'link':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'oauth_state_invalid', 'message': 'OAuth state is not valid for linking'},
        )

    if not resolved_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'oauth_provider_invalid', 'message': 'OAuth provider is not defined in state'},
        )

    target_user_id = state_payload_raw.get('target_user_id')
    if not isinstance(target_user_id, int) or target_user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'oauth_state_invalid', 'message': 'OAuth state target is invalid'},
        )

    return resolved_provider, state_payload_raw, target_user_id


async def _exchange_oauth_link_user_info(
    *,
    provider: str,
    request: LinkProviderCallbackRequest,
    state_payload: dict[str, object],
) -> OAuthUserInfo:
    oauth_provider = get_provider(provider)
    if not oauth_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'oauth_provider_invalid', 'message': f'OAuth provider "{provider}" is not enabled'},
        )

    try:
        exchange_kwargs: dict[str, str] = {'state': request.state}
        if provider == 'vk':
            if request.type and request.type != 'code_v2':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={'code': 'oauth_vk_type_invalid', 'message': 'Unsupported VK OAuth response type'},
                )
            if not request.device_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={'code': 'oauth_vk_device_missing', 'message': 'Missing VK device_id in callback'},
                )
            code_verifier = state_payload.get('code_verifier')
            if not isinstance(code_verifier, str) or not code_verifier:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={'code': 'oauth_vk_pkce_missing', 'message': 'Missing VK PKCE verifier'},
                )
            exchange_kwargs.update({'device_id': request.device_id, 'code_verifier': code_verifier})

        token_data = await oauth_provider.exchange_code(request.code, **exchange_kwargs)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('OAuth link code exchange failed', provider=provider, exc=exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'oauth_exchange_failed', 'message': 'Failed to exchange authorization code'},
        ) from exc

    try:
        return await oauth_provider.get_user_info(token_data)
    except Exception as exc:
        logger.error('OAuth link user info fetch failed', provider=provider, exc=exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'oauth_userinfo_failed', 'message': 'Failed to fetch user information from provider'},
        ) from exc


def _raise_identity_already_linked_conflict(provider: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            'code': 'link_code_identity_conflict',
            'message': f'{provider.capitalize()} is already linked to another account',
        },
    )


async def _link_oauth_identity(
    db: AsyncSession,
    *,
    user: User,
    provider: str,
    user_info: OAuthUserInfo,
) -> User:
    source_user = await get_user_by_oauth_provider(db, provider, user_info.provider_id)

    if source_user is None and user_info.email and user_info.email_verified:
        email_user = await get_user_by_email(db, user_info.email)
        if email_user:
            if email_user.id != user.id:
                _raise_identity_already_linked_conflict(provider)
            await set_user_oauth_provider_id(db, email_user, provider, user_info.provider_id)
            source_user = email_user

    if source_user is None:
        await set_user_oauth_provider_id(db, user, provider, user_info.provider_id)
        _fill_missing_profile_fields_from_oauth(user, user_info)
        return user

    if source_user.id == user.id:
        await set_user_oauth_provider_id(db, user, provider, user_info.provider_id)
        _fill_missing_profile_fields_from_oauth(user, user_info)
        return user

    _raise_identity_already_linked_conflict(provider)
    raise AssertionError('unreachable')


def _sync_telegram_profile_from_init_data(user: User, user_data: dict[str, object]) -> None:
    updated = False
    username = user_data.get('username')
    first_name = user_data.get('first_name')
    last_name = user_data.get('last_name')

    if isinstance(username, str) and username and username != user.username:
        user.username = username
        updated = True
    if isinstance(first_name, str) and first_name and first_name != user.first_name:
        user.first_name = first_name
        updated = True
    if isinstance(last_name, str) and last_name and last_name != user.last_name:
        user.last_name = last_name
        updated = True
    if user.telegram_id is not None:
        user.auth_type = 'telegram'
        updated = True
    if updated:
        user.updated_at = datetime.now(UTC).replace(tzinfo=None)


async def _link_telegram_identity(
    db: AsyncSession,
    *,
    user: User,
    telegram_id: int,
    user_data: dict[str, object],
) -> User:
    source_user = await get_user_by_telegram_id(db, telegram_id)
    await _ensure_telegram_attach_allowed(user, source_telegram_id=telegram_id)

    if source_user is None:
        user.telegram_id = telegram_id
        _sync_telegram_profile_from_init_data(user, user_data)
        return user

    await _ensure_telegram_relink_allowed(user, source_user)

    if source_user.id == user.id:
        _sync_telegram_profile_from_init_data(user, user_data)
        return user

    _raise_identity_already_linked_conflict('telegram')
    raise AssertionError('unreachable')


@router.get('/identities', response_model=LinkedIdentitiesResponse)
async def get_linked_identities(user: User = Depends(get_current_cabinet_user)):
    """Get linked login identities for current user."""
    hints = get_user_identity_hints(user)
    reasons = {provider: await _get_unlink_block_reason(user, provider) for provider in hints}
    identities: list[LinkedIdentity] = []
    for provider, provider_user_id_masked in sorted(hints.items()):
        blocked_reason = reasons.get(provider)
        blocked_until: datetime | None = None
        retry_after_seconds: int | None = None
        if blocked_reason == 'cooldown_active':
            cooldown_payload = await cache.get(_unlink_cooldown_key(user.id, provider))
            _, blocked_until, retry_after_seconds = _extract_cooldown_state(
                cooldown_payload,
                UNLINK_COOLDOWN_SECONDS,
            )

        identities.append(
            LinkedIdentity(
                provider=provider,
                provider_user_id_masked=provider_user_id_masked,
                can_unlink=blocked_reason is None,
                blocked_reason=blocked_reason,
                blocked_until=blocked_until,
                retry_after_seconds=retry_after_seconds,
            )
        )

    telegram_cooldown_payload = await cache.get(_telegram_relink_cooldown_key(user.id))
    telegram_cooldown_active, cooldown_until, relink_retry_after = _extract_cooldown_state(
        telegram_cooldown_payload,
        TELEGRAM_RELINK_COOLDOWN_SECONDS,
    )
    requires_unlink_first = user.telegram_id is not None

    return LinkedIdentitiesResponse(
        identities=identities,
        telegram_relink=TelegramRelinkStatus(
            can_start_relink=not requires_unlink_first and not telegram_cooldown_active,
            requires_unlink_first=requires_unlink_first,
            cooldown_until=cooldown_until if telegram_cooldown_active else None,
            retry_after_seconds=relink_retry_after if telegram_cooldown_active else None,
        ),
    )


@router.get('/link/result', response_model=PendingLinkResultResponse)
async def get_pending_link_result(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_link_result_security),
):
    """Consume pending external-browser link result for current user."""
    _ = request  # keep signature explicit for future audit/security hooks
    user_id = _get_link_result_user_id(credentials)
    payload = await cache.get(_link_result_key(user_id))
    if not isinstance(payload, dict):
        return PendingLinkResultResponse(pending=False)

    await cache.delete(_link_result_key(user_id))
    return PendingLinkResultResponse(
        pending=True,
        status=payload.get('status') if isinstance(payload.get('status'), str) else None,
        provider=payload.get('provider') if isinstance(payload.get('provider'), str) else None,
        message=payload.get('message') if isinstance(payload.get('message'), str) else None,
        code=payload.get('code') if isinstance(payload.get('code'), str) else None,
        auth_response=payload.get('auth_response') if isinstance(payload.get('auth_response'), dict) else None,
    )


@router.get('/link/oauth/{provider}/authorize', response_model=LinkProviderAuthorizeResponse)
async def get_link_provider_authorize_url(
    provider: str,
    user: User = Depends(get_current_cabinet_user),
):
    """Get OAuth authorize URL for direct account linking."""
    normalized_provider = provider.strip().lower()
    oauth_provider = get_provider(normalized_provider)
    if not oauth_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'oauth_provider_invalid',
                'message': f'OAuth provider "{normalized_provider}" is not enabled',
            },
        )

    state_payload: dict[str, object] = {
        'intent': 'link',
        'target_user_id': user.id,
    }
    if normalized_provider == 'vk':
        vk_payload, code_challenge = build_vk_pkce_payload()
        state_payload.update(vk_payload)
        state = await generate_oauth_state(normalized_provider, payload=state_payload)
        authorize_url = oauth_provider.get_authorization_url(state, code_challenge=code_challenge)
    else:
        state = await generate_oauth_state(normalized_provider, payload=state_payload)
        authorize_url = oauth_provider.get_authorization_url(state)

    return LinkProviderAuthorizeResponse(
        provider=normalized_provider,
        authorize_url=authorize_url,
        state=state,
    )


@router.post('/link/oauth/{provider}/callback', response_model=AuthResponse)
async def link_provider_callback(
    provider: str,
    request: LinkProviderCallbackRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Complete direct OAuth linking in the same authenticated browser session."""
    normalized_provider, state_payload, target_user_id = await _consume_link_oauth_state(
        state=request.state,
        provider=provider.strip().lower(),
    )
    if target_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': 'link_target_mismatch',
                'message': 'OAuth callback does not belong to current cabinet session',
            },
        )

    user_info = await _exchange_oauth_link_user_info(
        provider=normalized_provider,
        request=request,
        state_payload=state_payload,
    )
    primary_user = await _link_oauth_identity(
        db,
        user=user,
        provider=normalized_provider,
        user_info=user_info,
    )
    return await _finalize_link_auth_response(
        db,
        user=primary_user,
        provider=normalized_provider,
    )


@router.post('/link/oauth/server-complete', response_model=LinkOperationResponse)
async def link_provider_server_complete(
    request: LinkProviderCallbackRequest,
    db: AsyncSession = Depends(get_cabinet_db),
):
    """
    Complete OAuth linking without current JWT.
    Used when Mini App opens OAuth in an external browser and result is polled from the main app.
    """
    normalized_provider = 'oauth'
    target_user_id: int | None = None
    try:
        normalized_provider, state_payload, target_user_id = await _consume_link_oauth_state(
            state=request.state,
        )
        target_user = await get_user_by_id(db, target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={'code': 'link_target_missing', 'message': 'Target account not found'},
            )

        user_info = await _exchange_oauth_link_user_info(
            provider=normalized_provider,
            request=request,
            state_payload=state_payload,
        )
        primary_user = await _link_oauth_identity(
            db,
            user=target_user,
            provider=normalized_provider,
            user_info=user_info,
        )
        switched_account = primary_user.id != target_user.id
        if switched_account:
            auth_response = await _finalize_link_auth_response(
                db,
                user=primary_user,
                provider=normalized_provider,
            )
        else:
            primary_user.cabinet_last_login = datetime.now(UTC).replace(tzinfo=None)
            await db.commit()
            auth_response = None
        response = LinkOperationResponse(
            status='success',
            provider=normalized_provider,
            message='Identity linked successfully',
            code='identity_linked',
            switched_account=switched_account,
        )
        await _store_link_result(
            user_id=target_user_id,
            provider=normalized_provider,
            status_value=response.status,
            message=response.message,
            code=response.code,
            auth_response=auth_response,
        )
        return response
    except HTTPException as exc:
        detail = exc.detail
        code = _extract_detail_code(detail)
        message = _extract_detail_message(detail, 'Failed to link identity')
        status_value = _status_from_code(code)

        if target_user_id:
            await _store_link_result(
                user_id=target_user_id,
                provider=normalized_provider,
                status_value=status_value,
                message=message,
                code=code,
            )

        return LinkOperationResponse(
            status=status_value,
            provider=normalized_provider,
            message=message,
            code=code,
            switched_account=False,
        )


@router.post('/link/telegram', response_model=AuthResponse)
async def link_telegram_identity(
    request: TelegramAuthRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Link Telegram identity to current account using Telegram Mini App init data."""
    user_data = validate_telegram_init_data(request.init_data)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                'code': 'telegram_auth_invalid',
                'message': 'Invalid or expired Telegram authentication data',
            },
        )

    telegram_id = user_data.get('id')
    if not isinstance(telegram_id, int) or telegram_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'code': 'telegram_id_missing', 'message': 'Missing Telegram user ID'},
        )

    primary_user = await _link_telegram_identity(
        db,
        user=user,
        telegram_id=telegram_id,
        user_data=user_data,
    )
    return await _finalize_link_auth_response(
        db,
        user=primary_user,
        provider='telegram',
    )


@router.post('/identities/{provider}/unlink/request', response_model=UnlinkIdentityRequestResponse)
async def request_unlink_identity(
    provider: str,
    user: User = Depends(get_current_cabinet_user),
):
    """Start unlink flow and return short-lived request token for confirmation."""
    normalized_provider = provider.strip().lower()
    reason = await _get_unlink_block_reason(user, normalized_provider)
    if reason:
        status_code = status.HTTP_409_CONFLICT if reason != 'provider_not_supported' else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail={
                'code': 'unlink_not_allowed',
                'reason': reason,
                'message': 'Unlink is not allowed for this identity',
            },
        )

    cooldown_payload = await cache.get(_unlink_otp_send_cooldown_key(user.id, normalized_provider))
    if isinstance(cooldown_payload, dict) and cooldown_payload.get('active'):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                'code': 'unlink_otp_resend_cooldown',
                'message': 'Please wait before requesting another OTP code',
                'retry_after_seconds': UNLINK_OTP_SEND_COOLDOWN_SECONDS,
            },
        )

    blocked_payload = await cache.get(_unlink_otp_send_block_key(user.id, normalized_provider))
    if isinstance(blocked_payload, dict) and blocked_payload.get('active'):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                'code': 'unlink_otp_rate_limited',
                'message': 'Too many OTP requests for this identity. Try again later.',
            },
        )

    send_count = await cache.increment(_unlink_otp_send_counter_key(user.id, normalized_provider), 1)
    if send_count is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'code': 'unlink_otp_counter_error', 'message': 'Failed to validate OTP request limit'},
        )
    if send_count == 1:
        await cache.expire(_unlink_otp_send_counter_key(user.id, normalized_provider), UNLINK_OTP_SEND_WINDOW_SECONDS)
    if send_count > UNLINK_OTP_SEND_MAX_PER_WINDOW:
        await cache.set(
            _unlink_otp_send_block_key(user.id, normalized_provider),
            _build_cooldown_payload(UNLINK_OTP_SEND_WINDOW_SECONDS),
            expire=UNLINK_OTP_SEND_WINDOW_SECONDS,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                'code': 'unlink_otp_rate_limited',
                'message': 'Too many OTP requests for this identity. Try again later.',
            },
        )

    request_token = secrets.token_urlsafe(24)
    otp_code = _generate_otp_code()
    payload = {
        'user_id': user.id,
        'provider': normalized_provider,
        'requested_at': datetime.now(UTC).isoformat(),
        'otp_hash': _unlink_otp_hash(otp_code),
    }
    saved = await cache.set(_unlink_request_key(request_token), payload, expire=UNLINK_CONFIRM_TTL_SECONDS)
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'code': 'unlink_request_storage_error', 'message': 'Failed to create unlink request'},
        )

    if user.telegram_id is None:
        await cache.delete(_unlink_request_key(request_token))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': 'unlink_not_allowed',
                'reason': 'telegram_required',
                'message': 'Telegram is required for unlink confirmation',
            },
        )

    try:
        await _send_unlink_otp_to_telegram(user.telegram_id, normalized_provider, otp_code)
    except Exception as exc:
        await cache.delete(_unlink_request_key(request_token))
        # Roll back counter effect when delivery fails.
        await cache.increment(_unlink_otp_send_counter_key(user.id, normalized_provider), -1)
        logger.warning(
            'Failed to send unlink OTP to telegram',
            user_id=user.id,
            provider=normalized_provider,
            error=exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={'code': 'unlink_otp_delivery_failed', 'message': 'Failed to send OTP to Telegram'},
        ) from exc

    await cache.set(
        _unlink_otp_send_cooldown_key(user.id, normalized_provider),
        _build_cooldown_payload(UNLINK_OTP_SEND_COOLDOWN_SECONDS),
        expire=UNLINK_OTP_SEND_COOLDOWN_SECONDS,
    )

    return UnlinkIdentityRequestResponse(
        provider=normalized_provider,
        request_token=request_token,
        expires_in_seconds=UNLINK_CONFIRM_TTL_SECONDS,
    )


@router.post('/identities/{provider}/unlink/confirm', response_model=UnlinkIdentityResponse)
async def confirm_unlink_identity(
    provider: str,
    request: UnlinkIdentityConfirmRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Confirm identity unlink and revoke all refresh sessions for security."""
    normalized_provider = provider.strip().lower()
    payload = await cache.get(_unlink_request_key(request.request_token))
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'unlink_request_invalid', 'message': 'Unlink request is invalid or expired'},
        )

    if payload.get('user_id') != user.id or payload.get('provider') != normalized_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'unlink_request_mismatch',
                'message': 'Unlink request does not match current user/provider',
            },
        )

    otp_hash = payload.get('otp_hash')
    if not isinstance(otp_hash, str) or not otp_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'unlink_request_invalid', 'message': 'Unlink request payload is invalid'},
        )

    attempts = await cache.increment(_unlink_otp_attempts_key(request.request_token), 1)
    if attempts is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'code': 'unlink_otp_attempts_error', 'message': 'Failed to validate OTP attempts'},
        )
    if attempts == 1:
        await cache.expire(_unlink_otp_attempts_key(request.request_token), UNLINK_CONFIRM_TTL_SECONDS)
    if attempts > UNLINK_OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={'code': 'unlink_otp_attempts_exceeded', 'message': 'Too many OTP attempts'},
        )

    if _unlink_otp_hash(request.otp_code.strip()) != otp_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'unlink_otp_invalid', 'message': 'OTP code is invalid'},
        )

    reason = await _get_unlink_block_reason(user, normalized_provider)
    if reason:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': 'unlink_not_allowed',
                'reason': reason,
                'message': 'Unlink is not allowed for this identity',
            },
        )

    attr_name = _UNLINK_PROVIDER_ATTRS[normalized_provider]
    setattr(user, attr_name, None)
    user.updated_at = datetime.now(UTC).replace(tzinfo=None)

    # Security: invalidate refresh sessions after identity change.
    await db.execute(
        update(CabinetRefreshToken)
        .where(
            CabinetRefreshToken.user_id == user.id,
            CabinetRefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC).replace(tzinfo=None))
    )

    await db.commit()

    await cache.delete(_unlink_request_key(request.request_token))
    await cache.delete(_unlink_otp_attempts_key(request.request_token))
    await cache.set(
        _unlink_cooldown_key(user.id, normalized_provider),
        _build_cooldown_payload(UNLINK_COOLDOWN_SECONDS),
        expire=UNLINK_COOLDOWN_SECONDS,
    )
    if normalized_provider == 'telegram':
        await cache.set(
            _telegram_unlink_marker_key(user.id),
            _build_cooldown_payload(TELEGRAM_RELINK_COOLDOWN_SECONDS),
            expire=TELEGRAM_RELINK_COOLDOWN_SECONDS,
        )

    logger.info('Identity unlinked', user_id=user.id, provider=normalized_provider)
    return UnlinkIdentityResponse(message='Identity unlinked successfully', provider=normalized_provider)


@router.post('/link-code/create', response_model=LinkCodeCreateResponse)
async def create_account_link_code(user: User = Depends(get_current_cabinet_user)):
    """Create one-time code that can be used to link another account into current account."""
    if user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Only active accounts can create link codes',
        )
    code = await create_link_code(user)
    return LinkCodeCreateResponse(code=code, expires_in_seconds=LINK_CODE_TTL_SECONDS)


@router.post('/link-code/preview', response_model=LinkCodePreviewResponse)
async def preview_account_link_code(
    request: LinkCodePreviewRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Validate code and return source account hints before confirmation."""
    try:
        source_user_id = await preview_link_code(request.code, user.id)
    except LinkCodeAttemptsExceededError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeInvalidError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeConflictError as exc:
        raise _link_error_to_http(exc) from exc

    source_user = await get_user_by_id(db, source_user_id)
    if not source_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'link_code_user_not_found', 'message': 'Source account not found'},
        )
    if source_user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'code': 'link_code_source_inactive', 'message': 'Source account is not active'},
        )
    await _ensure_telegram_relink_allowed(user, source_user)

    return LinkCodePreviewResponse(
        source_user_id=source_user.id,
        source_identity_hints=get_user_identity_hints(source_user),
    )


@router.post('/link-code/confirm', response_model=AuthResponse)
async def confirm_account_link_code(
    request: LinkCodeConfirmRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Confirm linking: move identities to source account and return new auth session for source."""
    try:
        source_user_id = await preview_link_code(request.code, user.id)
    except LinkCodeAttemptsExceededError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeInvalidError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeConflictError as exc:
        raise _link_error_to_http(exc) from exc

    source_user_for_guard = await get_user_by_id(db, source_user_id)
    if not source_user_for_guard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'link_code_user_not_found', 'message': 'Source account not found'},
        )
    await _ensure_telegram_relink_allowed(user, source_user_for_guard)

    try:
        source_user = await confirm_link_code(db, request.code, user)
    except LinkCodeAttemptsExceededError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeInvalidError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeConflictError as exc:
        raise _link_error_to_http(exc) from exc

    source_user.cabinet_last_login = datetime.now(UTC).replace(tzinfo=None)
    await db.commit()
    auth_response = await _create_auth_response(source_user, db)
    await _store_refresh_token(db, source_user.id, auth_response.refresh_token, device_info='account-linking')

    logger.info('Account linking auth session switched to source account', source_user_id=source_user.id)

    # If user had recently unlinked Telegram and then linked another one, start 30-day change cooldown.
    if source_user.telegram_id is not None:
        unlink_marker = await cache.get(_telegram_unlink_marker_key(source_user.id))
        if isinstance(unlink_marker, dict) and unlink_marker.get('active'):
            await cache.set(
                _telegram_relink_cooldown_key(source_user.id),
                _build_cooldown_payload(TELEGRAM_RELINK_COOLDOWN_SECONDS),
                expire=TELEGRAM_RELINK_COOLDOWN_SECONDS,
            )
            await cache.delete(_telegram_unlink_marker_key(source_user.id))

    return auth_response


@router.post('/link-code/manual-request', response_model=ManualMergeResponse)
async def request_manual_merge(
    request: ManualMergeRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Create manual merge support ticket for disputed account linking cases."""
    if not settings.is_support_tickets_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'code': 'support_disabled', 'message': 'Support tickets are disabled'},
        )

    try:
        source_user_id = await preview_link_code(request.code, user.id)
    except (LinkCodeAttemptsExceededError, LinkCodeInvalidError, LinkCodeConflictError) as exc:
        raise _link_error_to_http(exc) from exc

    source_user = await get_user_by_id(db, source_user_id)
    if not source_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'link_code_user_not_found', 'message': 'Source account not found'},
        )
    await _ensure_telegram_relink_allowed(user, source_user)

    message_text = build_manual_merge_ticket_message(
        current_user_id=user.id,
        source_user_id=source_user.id,
        current_user_hints=get_user_identity_hints(user),
        source_user_hints=get_user_identity_hints(source_user),
        comment=request.comment,
    )

    ticket = Ticket(
        user_id=user.id,
        title=MANUAL_MERGE_TICKET_TITLE,
        status='open',
        priority='high',
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(ticket)
    await db.flush()

    initial_message = TicketMessage(
        ticket_id=ticket.id,
        user_id=user.id,
        message_text=message_text,
        is_from_admin=False,
        created_at=datetime.now(UTC),
    )
    db.add(initial_message)
    await db.commit()
    await db.refresh(ticket)

    try:
        await notify_admins_about_new_ticket(ticket, db)
    except Exception as exc:
        logger.warning('Failed to notify admins about manual merge ticket', ticket_id=ticket.id, error=exc)

    return ManualMergeResponse(
        message='Manual merge request has been sent to support',
        ticket_id=ticket.id,
    )


@router.get('/link-code/manual-request/latest', response_model=ManualMergeTicketStatusResponse | None)
async def get_latest_manual_merge_request(
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Return latest manual merge ticket status for current user."""
    stmt = (
        select(Ticket)
        .where(Ticket.user_id == user.id, Ticket.title == MANUAL_MERGE_TICKET_TITLE)
        .options(selectinload(Ticket.messages))
        .order_by(desc(Ticket.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()
    if ticket is None:
        return None

    source_user_id: int | None = None
    current_user_id: int | None = None
    decision: str | None = None
    resolution_comment: str | None = None

    for message in ticket.messages:
        if not message.message_text:
            continue
        payload = parse_manual_merge_payload(message.message_text)
        if payload:
            source_user_id = payload['source_user_id']
            current_user_id = payload['current_user_id']
        resolution = parse_manual_merge_resolution(message.message_text)
        if resolution:
            decision = str(resolution['action'])
            resolution_comment = str(resolution.get('comment')) if resolution.get('comment') else None

    return ManualMergeTicketStatusResponse(
        ticket_id=ticket.id,
        status=ticket.status,
        decision=decision,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at or ticket.created_at,
        source_user_id=source_user_id,
        current_user_id=current_user_id,
        resolution_comment=resolution_comment,
    )
