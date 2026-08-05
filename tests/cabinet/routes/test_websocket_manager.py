from unittest.mock import AsyncMock

import pytest

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
