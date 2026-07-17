from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.cabinet.auth.oauth_providers import OAuthUserInfo


pytestmark = pytest.mark.asyncio


def _load_account_linking_module():
    return importlib.import_module('app.cabinet.routes.account_linking')


account_linking = _load_account_linking_module()


def build_user(user_id: int, *, telegram_id: int | None = None, email: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        telegram_id=telegram_id,
        first_name=None,
        last_name=None,
        username=None,
        email=email,
        email_verified=False,
        email_verified_at=None,
        updated_at=None,
        auth_type='email',
    )


def build_user_info(
    *,
    provider: str = 'yandex',
    provider_id: str = 'provider-1',
    email: str | None = None,
    email_verified: bool = False,
) -> OAuthUserInfo:
    return OAuthUserInfo(
        provider=provider,
        provider_id=provider_id,
        email=email,
        email_verified=email_verified,
        username='linked-user',
        first_name='Linked',
        last_name='User',
    )


async def test_link_oauth_identity_rejects_provider_owned_by_other_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = build_user(1)
    foreign_user = build_user(2)

    monkeypatch.setattr(
        account_linking,
        'get_user_by_oauth_provider',
        AsyncMock(return_value=foreign_user),
    )
    monkeypatch.setattr(account_linking, 'get_user_by_email', AsyncMock(return_value=None))
    set_provider_mock = AsyncMock()
    monkeypatch.setattr(account_linking, 'set_user_oauth_provider_id', set_provider_mock)

    with pytest.raises(HTTPException) as exc_info:
        await account_linking._link_oauth_identity(
            SimpleNamespace(),
            user=current_user,
            provider='yandex',
            user_info=build_user_info(provider_id='ya-1'),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail['code'] == 'link_code_identity_conflict'
    set_provider_mock.assert_not_awaited()


async def test_link_oauth_identity_rejects_verified_email_owned_by_other_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = build_user(1, email='current@example.com')
    foreign_user = build_user(2, email='shared@example.com')

    monkeypatch.setattr(account_linking, 'get_user_by_oauth_provider', AsyncMock(return_value=None))
    monkeypatch.setattr(
        account_linking,
        'get_user_by_email',
        AsyncMock(return_value=foreign_user),
    )
    set_provider_mock = AsyncMock()
    monkeypatch.setattr(account_linking, 'set_user_oauth_provider_id', set_provider_mock)

    with pytest.raises(HTTPException) as exc_info:
        await account_linking._link_oauth_identity(
            SimpleNamespace(),
            user=current_user,
            provider='google',
            user_info=build_user_info(
                provider_id='google-1',
                email='shared@example.com',
                email_verified=True,
            ),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail['code'] == 'link_code_identity_conflict'
    set_provider_mock.assert_not_awaited()


async def test_link_oauth_identity_keeps_same_user_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = build_user(7, email='same@example.com')

    monkeypatch.setattr(
        account_linking,
        'get_user_by_oauth_provider',
        AsyncMock(return_value=current_user),
    )
    monkeypatch.setattr(account_linking, 'get_user_by_email', AsyncMock(return_value=None))
    set_provider_mock = AsyncMock()
    monkeypatch.setattr(account_linking, 'set_user_oauth_provider_id', set_provider_mock)

    result = await account_linking._link_oauth_identity(
        SimpleNamespace(),
        user=current_user,
        provider='vk',
        user_info=build_user_info(provider_id='vk-1'),
    )

    assert result is current_user
    set_provider_mock.assert_awaited_once()


async def test_link_telegram_identity_rejects_foreign_telegram(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = build_user(1)
    foreign_user = build_user(2, telegram_id=777)

    monkeypatch.setattr(
        account_linking,
        'get_user_by_telegram_id',
        AsyncMock(return_value=foreign_user),
    )
    monkeypatch.setattr(account_linking, '_ensure_telegram_attach_allowed', AsyncMock())
    monkeypatch.setattr(account_linking, '_ensure_telegram_relink_allowed', AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        await account_linking._link_telegram_identity(
            SimpleNamespace(),
            user=current_user,
            telegram_id=777,
            user_data={'id': 777, 'username': 'linked'},
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail['code'] == 'link_code_identity_conflict'


async def test_confirm_link_code_awaits_auth_response_with_database(monkeypatch: pytest.MonkeyPatch) -> None:
    current_user = build_user(1)
    current_user.status = 'active'
    source_user = build_user(2)
    source_user.status = 'active'
    source_user.cabinet_last_login = None
    db = SimpleNamespace(commit=AsyncMock())
    auth_response = SimpleNamespace(refresh_token='refresh-token')
    create_auth_response = AsyncMock(return_value=auth_response)
    store_refresh_token = AsyncMock()

    monkeypatch.setattr(account_linking, 'preview_link_code', AsyncMock(return_value=source_user.id))
    monkeypatch.setattr(account_linking, 'get_user_by_id', AsyncMock(return_value=source_user))
    monkeypatch.setattr(account_linking, '_ensure_telegram_relink_allowed', AsyncMock())
    monkeypatch.setattr(account_linking, 'confirm_link_code', AsyncMock(return_value=source_user))
    monkeypatch.setattr(account_linking, '_create_auth_response', create_auth_response)
    monkeypatch.setattr(account_linking, '_store_refresh_token', store_refresh_token)

    result = await account_linking.confirm_account_link_code(
        account_linking.LinkCodeConfirmRequest(code='123456'),
        user=current_user,
        db=db,
    )

    assert result is auth_response
    create_auth_response.assert_awaited_once_with(source_user, db)
    store_refresh_token.assert_awaited_once_with(
        db,
        source_user.id,
        auth_response.refresh_token,
        device_info='account-linking',
    )
