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
