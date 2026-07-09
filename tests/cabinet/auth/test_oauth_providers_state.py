from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.cabinet.auth import oauth_providers


pytestmark = pytest.mark.asyncio


async def test_peek_oauth_state_any_does_not_consume_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    state = 'state-peek'
    cache_key = oauth_providers.cache_key('oauth_state', state)
    cache = SimpleNamespace(
        get=AsyncMock(return_value=json.dumps({'provider': 'yandex', 'intent': 'login'})),
        delete=AsyncMock(),
    )
    monkeypatch.setattr(oauth_providers, 'cache', cache)

    payload = await oauth_providers.peek_oauth_state_any(state)

    assert payload == {'provider': 'yandex', 'intent': 'login'}
    cache.get.assert_awaited_once_with(cache_key)
    cache.delete.assert_not_awaited()


async def test_consume_oauth_state_any_returns_json_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    state = 'state-123'
    cache_key = oauth_providers.cache_key('oauth_state', state)
    cache = SimpleNamespace(
        get=AsyncMock(return_value=json.dumps({'provider': 'yandex', 'intent': 'link', 'target_user_id': 42})),
        delete=AsyncMock(),
    )
    monkeypatch.setattr(oauth_providers, 'cache', cache)

    payload = await oauth_providers.consume_oauth_state_any(state)

    assert payload == {'provider': 'yandex', 'intent': 'link', 'target_user_id': 42}
    cache.get.assert_awaited_once_with(cache_key)
    cache.delete.assert_awaited_once_with(cache_key)


async def test_consume_oauth_state_any_preserves_legacy_plain_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    state = 'legacy-state'
    cache_key = oauth_providers.cache_key('oauth_state', state)
    cache = SimpleNamespace(get=AsyncMock(return_value='vk'), delete=AsyncMock())
    monkeypatch.setattr(oauth_providers, 'cache', cache)

    payload = await oauth_providers.consume_oauth_state_any(state)

    assert payload == {'provider': 'vk'}
    cache.get.assert_awaited_once_with(cache_key)
    cache.delete.assert_awaited_once_with(cache_key)


async def test_consume_oauth_state_rejects_provider_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    state = 'state-mismatch'
    cache_key = oauth_providers.cache_key('oauth_state', state)
    cache = SimpleNamespace(
        get=AsyncMock(return_value=json.dumps({'provider': 'google', 'intent': 'login'})),
        delete=AsyncMock(),
    )
    monkeypatch.setattr(oauth_providers, 'cache', cache)

    payload = await oauth_providers.consume_oauth_state(state, 'yandex')

    assert payload is None
    cache.get.assert_awaited_once_with(cache_key)
    cache.delete.assert_awaited_once_with(cache_key)
