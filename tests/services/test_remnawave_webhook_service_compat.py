from types import SimpleNamespace, TracebackType
from typing import Any
from unittest.mock import AsyncMock

import pytest

import app.services.remnawave_webhook_service as webhook_module
from app.services.remnawave_webhook_service import RemnaWaveWebhookService
from app.utils.miniapp_buttons import CALLBACK_TO_CABINET_PATH


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


def test_build_traffic_warning_context_uses_current_remnawave_payload() -> None:
    context = RemnaWaveWebhookService._build_traffic_warning_context(
        {
            'trafficLimitBytes': 100 * 1024**3,
            'userTraffic': {'usedTrafficBytes': 84.5 * 1024**3},
        },
        None,
    )

    assert context is not None
    assert context['actual_percent'] == pytest.approx(84.5)
    assert context['percent'] == '84.5'
    assert context['used_gb'] == '84.5'
    assert context['limit_gb'] == '100'
    assert context['remaining_gb'] == '15.5'


def test_buy_traffic_button_deep_links_to_expanded_topup() -> None:
    assert CALLBACK_TO_CABINET_PATH['buy_traffic'] == '/subscription?trafficTopUp=1#ultima-traffic-top-up'


@pytest.mark.asyncio
async def test_bandwidth_warning_uses_custom_message_and_buy_traffic_button(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = RemnaWaveWebhookService(bot=SimpleNamespace())
    service._notify_user = AsyncMock()
    db = SimpleNamespace(commit=AsyncMock())
    user = SimpleNamespace(
        id=7,
        language='ru',
        notification_settings={'traffic_warning_enabled': True, 'traffic_warning_percent': 80},
    )
    subscription = SimpleNamespace(traffic_used_gb=0.0, traffic_limit_gb=100)
    custom_message = 'Осталось {remaining_gb} ГБ из {limit_gb} ГБ'
    monkeypatch.setattr(webhook_module.settings, 'ULTIMA_TRAFFIC_WARNING_MESSAGE_RU', custom_message)

    await service._handle_bandwidth_threshold(
        db,
        user,
        subscription,
        {
            'trafficLimitBytes': 100 * 1024**3,
            'userTraffic': {'usedTrafficBytes': 85 * 1024**3},
        },
    )

    db.commit.assert_awaited_once()
    service._notify_user.assert_awaited_once()
    call = service._notify_user.await_args
    assert call.args[1] == 'WEBHOOK_SUB_BANDWIDTH_THRESHOLD'
    assert call.kwargs['message_override'] == custom_message
    assert call.kwargs['format_kwargs']['remaining_gb'] == '15'
    assert call.kwargs['reply_markup'].inline_keyboard[0][0].callback_data == 'buy_traffic'
    assert subscription.traffic_used_gb == 85


@pytest.mark.asyncio
async def test_bandwidth_warning_respects_user_threshold() -> None:
    service = RemnaWaveWebhookService(bot=SimpleNamespace())
    service._notify_user = AsyncMock()
    db = SimpleNamespace(commit=AsyncMock())
    user = SimpleNamespace(
        id=7,
        language='ru',
        notification_settings={'traffic_warning_enabled': True, 'traffic_warning_percent': 90},
    )
    subscription = SimpleNamespace(traffic_used_gb=0.0, traffic_limit_gb=100)

    await service._handle_bandwidth_threshold(
        db,
        user,
        subscription,
        {
            'trafficLimitBytes': 100 * 1024**3,
            'userTraffic': {'usedTrafficBytes': 85 * 1024**3},
        },
    )

    db.commit.assert_not_awaited()
    service._notify_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_bandwidth_warning_respects_user_opt_out() -> None:
    service = RemnaWaveWebhookService(bot=SimpleNamespace())
    service._notify_user = AsyncMock()
    db = SimpleNamespace(commit=AsyncMock())
    user = SimpleNamespace(
        id=7,
        language='ru',
        notification_settings={'traffic_warning_enabled': False},
    )

    await service._handle_bandwidth_threshold(db, user, None, {'thresholdPercent': 95})

    service._notify_user.assert_not_awaited()
