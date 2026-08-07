import asyncio
from unittest.mock import AsyncMock

import pytest

import app.cabinet.routes.websocket as websocket_module
from app.cabinet.routes.websocket import CabinetConnectionManager


pytestmark = pytest.mark.asyncio


async def test_send_to_user_reports_no_delivery_without_connection():
    manager = CabinetConnectionManager()

    delivered = await manager.send_to_user(42, {'type': 'notification.test'})

    assert delivered is False


async def test_send_to_user_reports_success_for_connected_client():
    manager = CabinetConnectionManager()
    websocket = AsyncMock()
    await manager.connect(websocket, user_id=42, is_admin=False)

    delivered = await manager.send_to_user(42, {'type': 'notification.test'})

    assert delivered is True
    websocket.send_text.assert_awaited_once()


async def test_guest_connections_are_scoped_to_ticket():
    manager = CabinetConnectionManager()
    first = AsyncMock()
    second = AsyncMock()
    await manager.connect_guest(first, ticket_id=10)
    await manager.connect_guest(second, ticket_id=20)

    delivered = await manager.send_to_guest(10, {'type': 'ticket.admin_reply'})

    assert delivered is True
    first.send_text.assert_awaited_once()
    second.send_text.assert_not_awaited()


async def test_guest_disconnect_removes_delivery_target():
    manager = CabinetConnectionManager()
    websocket = AsyncMock()
    await manager.connect_guest(websocket, ticket_id=10)
    await manager.disconnect_guest(websocket, ticket_id=10)

    delivered = await manager.send_to_guest(10, {'type': 'ticket.admin_reply'})

    assert delivered is False
    websocket.send_text.assert_not_awaited()


async def test_slow_connection_times_out_without_blocking_other_clients(monkeypatch):
    manager = CabinetConnectionManager()
    slow = AsyncMock()
    fast = AsyncMock()

    async def wait_forever(_data):
        await asyncio.Event().wait()

    slow.send_text.side_effect = wait_forever
    monkeypatch.setattr(websocket_module, '_WS_SEND_TIMEOUT_SECONDS', 0.01)
    await manager.connect(slow, user_id=42, is_admin=False)
    await manager.connect(fast, user_id=42, is_admin=False)

    delivered = await manager.send_to_user(42, {'type': 'notification.test'})

    assert delivered is True
    fast.send_text.assert_awaited_once()


async def test_broker_event_is_delivered_only_locally():
    manager = CabinetConnectionManager()
    manager._send_to_user_local = AsyncMock(return_value=True)  # type: ignore[method-assign]
    manager._publish = AsyncMock()  # type: ignore[method-assign]

    await manager._handle_broker_message(
        {
            'origin': 'another-process',
            'target_type': 'user',
            'target_id': 42,
            'message': {'type': 'notification.test'},
        }
    )

    manager._send_to_user_local.assert_awaited_once_with(42, {'type': 'notification.test'})
    manager._publish.assert_not_awaited()
