from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

import app.cabinet.routes.auth as auth_routes
from app.cabinet.schemas.auth import (
    EmailRegisterStandaloneRequest,
    EmailResendStandaloneRequest,
    EmailVerifyRequest,
    RefreshTokenRequest,
)


@pytest.mark.asyncio
async def test_auth_rate_limit_checks_ip_and_identifier(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = AsyncMock(side_effect=[False, True])
    monkeypatch.setattr(auth_routes.RateLimitCache, 'is_rate_limited', limiter)
    request = SimpleNamespace(client=SimpleNamespace(host='203.0.113.10'))

    with pytest.raises(HTTPException) as error:
        await auth_routes._enforce_auth_rate_limit(
            request,
            action='email_login',
            identifier='User@Example.com',
            identifier_limit=10,
            ip_limit=60,
            window=300,
        )

    assert error.value.status_code == 429
    assert limiter.await_count == 2
    assert limiter.await_args_list[0].args[:2] == ('ip:203.0.113.10', 'auth_email_login_ip')
    assert limiter.await_args_list[1].args[0].startswith('id:')


def test_auth_rate_limit_uses_forwarded_ip_from_private_proxy() -> None:
    request = SimpleNamespace(
        client=SimpleNamespace(host='172.18.0.2'),
        headers={'x-forwarded-for': '198.51.100.25, 172.18.0.2'},
    )

    assert auth_routes._get_auth_client_ip(request) == '198.51.100.25'


def test_auth_rate_limit_ignores_spoofed_forwarded_prefix() -> None:
    request = SimpleNamespace(
        client=SimpleNamespace(host='172.18.0.2'),
        headers={'x-forwarded-for': '203.0.113.99, 198.51.100.25, 172.18.0.2'},
    )

    assert auth_routes._get_auth_client_ip(request) == '198.51.100.25'


@pytest.mark.asyncio
async def test_refresh_token_is_rotated_atomically(monkeypatch: pytest.MonkeyPatch) -> None:
    old_token = 'old-refresh-token'
    new_token = 'new-refresh-token'
    token_record = SimpleNamespace(
        user_id=7,
        revoked_at=None,
        device_info='test-device',
        is_valid=True,
    )
    user = SimpleNamespace(id=7, telegram_id=700, status='active')
    result = SimpleNamespace(scalar_one_or_none=lambda: token_record)
    db = SimpleNamespace(execute=AsyncMock(return_value=result), add=Mock(), commit=AsyncMock())

    monkeypatch.setattr(auth_routes, '_enforce_auth_rate_limit', AsyncMock())
    monkeypatch.setattr(auth_routes, 'get_token_payload', Mock(return_value={'sub': '7'}))
    monkeypatch.setattr(auth_routes, 'get_user_by_id', AsyncMock(return_value=user))
    monkeypatch.setattr(auth_routes.UserRoleCRUD, 'get_user_permissions', AsyncMock(return_value=([], [], 0)))
    monkeypatch.setattr(auth_routes, 'create_access_token', Mock(return_value='new-access-token'))
    monkeypatch.setattr(auth_routes, 'create_refresh_token', Mock(return_value=new_token))
    monkeypatch.setattr(
        auth_routes,
        'get_refresh_token_expires_at',
        Mock(return_value=datetime.now(UTC) + timedelta(days=7)),
    )

    response = await auth_routes.refresh_token(
        RefreshTokenRequest(refresh_token=old_token),
        SimpleNamespace(client=SimpleNamespace(host='203.0.113.10')),
        db,
    )

    assert response.access_token == 'new-access-token'
    assert response.refresh_token == new_token
    assert token_record.revoked_at is not None
    new_record = db.add.call_args.args[0]
    assert new_record.user_id == user.id
    assert new_record.device_info == 'test-device'
    assert new_record.token_hash != old_token
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize('user_status', ['active', 'deleted'])
async def test_existing_unverified_registration_resends_verification(
    monkeypatch: pytest.MonkeyPatch, user_status: str
) -> None:
    user = SimpleNamespace(
        id=17,
        email='user@example.com',
        email_verified=False,
        password_hash='hashed',
        auth_type='email',
        status=user_status,
        email_verification_token='old-token',
        email_verification_expires=None,
        language='ru',
        first_name='User',
    )
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: user)),
        commit=AsyncMock(),
    )
    send_verification = AsyncMock(return_value=True)
    create_user = AsyncMock()
    monkeypatch.setattr(auth_routes, '_enforce_auth_rate_limit', AsyncMock())
    monkeypatch.setattr(auth_routes.disposable_email_service, 'is_disposable', Mock(return_value=False))
    monkeypatch.setattr(type(auth_routes.settings), 'is_test_email', Mock(return_value=False))
    monkeypatch.setattr(
        type(auth_routes.settings),
        'is_cabinet_email_verification_enabled',
        Mock(return_value=True),
    )
    monkeypatch.setattr(auth_routes, 'generate_verification_token', Mock(return_value='new-token'))
    monkeypatch.setattr(
        auth_routes,
        'get_verification_expires_at',
        Mock(return_value=datetime.now(UTC) + timedelta(hours=24)),
    )
    monkeypatch.setattr(auth_routes, '_send_verification_email', send_verification)
    monkeypatch.setattr(auth_routes, 'create_user_by_email', create_user)

    response = await auth_routes.register_email_standalone(
        EmailRegisterStandaloneRequest(email='User@Example.com', password='strong-password', language='ru'),
        SimpleNamespace(client=SimpleNamespace(host='203.0.113.10')),
        db,
    )

    assert response.requires_verification is True
    assert response.email == 'user@example.com'
    assert user.email_verification_token == 'new-token'
    db.commit.assert_awaited_once()
    send_verification.assert_awaited_once()
    create_user.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('user_status', ['active', 'deleted'])
async def test_public_resend_rotates_token_for_unverified_account(
    monkeypatch: pytest.MonkeyPatch, user_status: str
) -> None:
    user = SimpleNamespace(
        id=18,
        email='user@example.com',
        email_verified=False,
        password_hash='hashed',
        auth_type='email',
        status=user_status,
        email_verification_token='old-token',
        email_verification_expires=None,
    )
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: user)),
        commit=AsyncMock(),
    )
    send_verification = AsyncMock(return_value=True)
    monkeypatch.setattr(auth_routes, '_enforce_auth_rate_limit', AsyncMock())
    monkeypatch.setattr(
        type(auth_routes.settings),
        'is_cabinet_email_verification_enabled',
        Mock(return_value=True),
    )
    monkeypatch.setattr(auth_routes.email_service, 'is_configured', Mock(return_value=True))
    monkeypatch.setattr(auth_routes, 'generate_verification_token', Mock(return_value='new-token'))
    monkeypatch.setattr(
        auth_routes,
        'get_verification_expires_at',
        Mock(return_value=datetime.now(UTC) + timedelta(hours=24)),
    )
    monkeypatch.setattr(auth_routes, '_send_verification_email', send_verification)

    response = await auth_routes.resend_verification_standalone(
        EmailResendStandaloneRequest(email='User@Example.com'),
        SimpleNamespace(client=SimpleNamespace(host='203.0.113.10')),
        db,
    )

    assert response['message'].startswith('If this email')
    assert user.email_verification_token == 'new-token'
    db.commit.assert_awaited_once()
    send_verification.assert_awaited_once_with(db, user, 'new-token', email='user@example.com')


@pytest.mark.asyncio
async def test_verify_email_reactivates_recoverable_deleted_account(monkeypatch: pytest.MonkeyPatch) -> None:
    user = SimpleNamespace(
        id=19,
        email='user@example.com',
        email_verified=False,
        email_verified_at=None,
        password_hash='hashed',
        auth_type='email',
        status='deleted',
        email_verification_token='valid-token',
        email_verification_expires=datetime.now(UTC) + timedelta(hours=1),
        cabinet_last_login=None,
    )
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: user)),
        commit=AsyncMock(),
    )
    auth_response = SimpleNamespace(campaign_bonus=None, user=None, refresh_token='refresh-token')
    monkeypatch.setattr(auth_routes, '_sync_subscription_from_panel_by_email', AsyncMock())
    monkeypatch.setattr(auth_routes, '_create_auth_response', AsyncMock(return_value=auth_response))
    monkeypatch.setattr(auth_routes, '_store_refresh_token', AsyncMock())
    monkeypatch.setattr(auth_routes, '_process_campaign_bonus', AsyncMock(return_value=None))

    response = await auth_routes.verify_email(EmailVerifyRequest(token='valid-token'), db)

    assert response is auth_response
    assert user.status == 'active'
    assert user.email_verified is True
    assert user.email_verification_token is None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_public_resend_does_not_reveal_missing_account(monkeypatch: pytest.MonkeyPatch) -> None:
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None)),
        commit=AsyncMock(),
    )
    send_verification = AsyncMock()
    monkeypatch.setattr(auth_routes, '_enforce_auth_rate_limit', AsyncMock())
    monkeypatch.setattr(
        type(auth_routes.settings),
        'is_cabinet_email_verification_enabled',
        Mock(return_value=True),
    )
    monkeypatch.setattr(auth_routes.email_service, 'is_configured', Mock(return_value=True))
    monkeypatch.setattr(auth_routes, '_send_verification_email', send_verification)

    response = await auth_routes.resend_verification_standalone(
        EmailResendStandaloneRequest(email='missing@example.com'),
        SimpleNamespace(client=SimpleNamespace(host='203.0.113.10')),
        db,
    )

    assert response['message'].startswith('If this email')
    db.commit.assert_not_awaited()
    send_verification.assert_not_awaited()
