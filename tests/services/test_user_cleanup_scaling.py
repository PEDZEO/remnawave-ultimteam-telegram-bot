from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.services.user_service as user_service_module
from app.services.user_service import UserService


pytestmark = pytest.mark.asyncio


async def test_cleanup_inactive_users_uses_keyset_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    pages = [
        [
            SimpleNamespace(id=10, subscription=None),
            SimpleNamespace(id=20, subscription=SimpleNamespace(is_active=True)),
        ],
        [SimpleNamespace(id=30, subscription=None)],
        [],
    ]
    fetch = AsyncMock(side_effect=pages)
    monkeypatch.setattr(user_service_module, 'get_inactive_users', fetch)
    service = UserService()
    service.delete_user_account = AsyncMock(return_value=True)  # type: ignore[method-assign]

    deleted, skipped = await service.cleanup_inactive_users(SimpleNamespace(), months=3)

    assert (deleted, skipped) == (2, 1)
    assert [call.kwargs['after_id'] for call in fetch.await_args_list] == [0, 20, 30]
    assert all(call.kwargs['limit'] == 500 for call in fetch.await_args_list)
    assert [call.args[1] for call in service.delete_user_account.await_args_list] == [10, 30]
