from types import SimpleNamespace, TracebackType
from typing import Any

import pytest

import app.services.remnawave_webhook_service as webhook_module
from app.services.remnawave_webhook_service import RemnaWaveWebhookService


@pytest.mark.asyncio
async def test_resolve_user_by_panel_user_id(monkeypatch: pytest.MonkeyPatch) -> None:
    bot_user = SimpleNamespace(id=7, remnawave_uuid='rw-user-uuid')
    subscription = SimpleNamespace(id=99)
    panel_user = SimpleNamespace(uuid='rw-user-uuid')

    async def fake_get_user_by_telegram_id(db: Any, telegram_id: int) -> Any:
        return None

    async def fake_get_user_by_remnawave_uuid(db: Any, uuid: str) -> Any:
        if uuid == 'rw-user-uuid':
            return bot_user
        return None

    async def fake_get_subscription_by_user_id(db: Any, user_id: int) -> Any:
        assert user_id == bot_user.id
        return subscription

    class FakeRemnaWaveApi:
        async def get_user_by_id(self, user_id: int) -> Any:
            assert user_id == 42
            return panel_user

    class FakeApiContext:
        async def __aenter__(self) -> FakeRemnaWaveApi:
            return FakeRemnaWaveApi()

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            return None

    class FakeRemnaWaveService:
        is_configured = True

        def get_api_client(self) -> FakeApiContext:
            return FakeApiContext()

    monkeypatch.setattr(webhook_module, 'get_user_by_telegram_id', fake_get_user_by_telegram_id)
    monkeypatch.setattr(webhook_module, 'get_user_by_remnawave_uuid', fake_get_user_by_remnawave_uuid)
    monkeypatch.setattr(webhook_module, 'get_subscription_by_user_id', fake_get_subscription_by_user_id)
    monkeypatch.setattr('app.services.remnawave_service.RemnaWaveService', FakeRemnaWaveService)

    service = RemnaWaveWebhookService(bot=SimpleNamespace())

    resolved_user, resolved_subscription = await service._resolve_user_and_subscription(
        SimpleNamespace(),
        {'userId': 42},
    )

    assert resolved_user is bot_user
    assert resolved_subscription is subscription
