from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.cabinet.routes import oauth


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    ('payload', 'expected_intent'),
    [
        ({'provider': 'yandex'}, 'login'),
        ({'provider': 'yandex', 'intent': 'link', 'target_user_id': 42}, 'link'),
    ],
)
async def test_oauth_state_context_resolves_without_consuming(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
    expected_intent: str,
) -> None:
    peek_mock = AsyncMock(return_value=payload)
    monkeypatch.setattr(oauth, 'peek_oauth_state_any', peek_mock)
    monkeypatch.setattr(oauth, 'get_provider', lambda provider: object() if provider == 'yandex' else None)

    response = await oauth.get_oauth_state_context(oauth.OAuthStateContextRequest(state='valid-state'))

    assert response.provider == 'yandex'
    assert response.intent == expected_intent
    peek_mock.assert_awaited_once_with('valid-state')


async def test_oauth_state_context_rejects_expired_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oauth, 'peek_oauth_state_any', AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await oauth.get_oauth_state_context(oauth.OAuthStateContextRequest(state='expired-state'))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == 'Invalid or expired OAuth state'


async def test_oauth_login_syncs_existing_panel_subscription(monkeypatch: pytest.MonkeyPatch) -> None:
    db = AsyncMock()
    user = type('UserStub', (), {'id': 42, 'cabinet_last_login': None})()
    sync_mock = AsyncMock()
    create_auth_mock = AsyncMock(side_effect=RuntimeError('stop after sync'))
    monkeypatch.setattr(oauth, '_sync_subscription_from_panel_by_email', sync_mock)
    monkeypatch.setattr(oauth, '_create_auth_response', create_auth_mock)

    with pytest.raises(RuntimeError, match='stop after sync'):
        await oauth._finalize_oauth_login(db, user, 'yandex')

    sync_mock.assert_awaited_once_with(db, user)
    create_auth_mock.assert_awaited_once_with(user, db)
