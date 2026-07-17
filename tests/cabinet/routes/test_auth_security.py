from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

import app.cabinet.routes.auth as auth_routes
from app.cabinet.schemas.auth import RefreshTokenRequest


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
