from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.admin_notification_service import AdminNotificationService


def _make_service() -> tuple[AdminNotificationService, AsyncMock]:
    send_message = AsyncMock()
    service = AdminNotificationService(SimpleNamespace(send_message=send_message))
    service.chat_id = '-1002835894832'
    service.topic_id = 2
    service.ticket_topic_id = 126
    service.trial_topic_id = 35243
    service.payment_topic_id = 35241
    service.node_topic_id = 1649
    service.error_topic_id = 35257
    return service, send_message


def test_explicit_topic_has_priority_over_ticket_and_default_topics():
    service, _ = _make_service()

    assert service._resolve_topic_id(topic_id=35243) == 35243
    assert service._resolve_topic_id(ticket_event=True, topic_id=35241) == 35241
    assert service._resolve_topic_id(ticket_event=True) == 126
    assert service._resolve_topic_id() == 2
    assert service.node_topic_id == 1649
    assert service.error_topic_id == 35257


@pytest.mark.asyncio
async def test_send_message_passes_explicit_topic_to_telegram():
    service, send_message = _make_service()

    assert await service._send_message('Проверка', topic_id=35241) is True

    assert send_message.await_args.kwargs['chat_id'] == '-1002835894832'
    assert send_message.await_args.kwargs['message_thread_id'] == 35241
