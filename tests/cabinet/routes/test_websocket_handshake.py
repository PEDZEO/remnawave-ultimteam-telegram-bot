from unittest.mock import AsyncMock

import pytest
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from app.cabinet.routes import websocket as module


def _websocket():
    send = AsyncMock()
    websocket = WebSocket(
        {
            'type': 'websocket',
            'headers': [(b'sec-websocket-protocol', b'cabinet-auth, test-token')],
            'client': ('127.0.0.1', 1234),
        },
        receive=AsyncMock(return_value={'type': 'websocket.connect'}),
        send=send,
    )
    return websocket, send


@pytest.mark.asyncio
@pytest.mark.parametrize('already_accepted', [False, True])
async def test_endpoint_accepts_only_once_and_cleans_up(monkeypatch, already_accepted):
    websocket, send = _websocket()
    if already_accepted:
        await websocket.accept(subprotocol='cabinet-auth')
    monkeypatch.setattr(module, 'verify_cabinet_ws_token', AsyncMock(return_value=(42, False)))
    connect = AsyncMock()
    disconnect = AsyncMock()
    monkeypatch.setattr(module.cabinet_ws_manager, 'connect', connect)
    monkeypatch.setattr(module.cabinet_ws_manager, 'disconnect', disconnect)
    monkeypatch.setattr(websocket, 'receive_text', AsyncMock(side_effect=WebSocketDisconnect()))

    await module.cabinet_websocket_endpoint(websocket)

    assert sum(call.args[0]['type'] == 'websocket.accept' for call in send.await_args_list) == 1
    connect.assert_awaited_once_with(websocket, 42, False)
    disconnect.assert_awaited_once_with(websocket, 42)


@pytest.mark.asyncio
async def test_endpoint_does_not_register_connection_closed_during_auth(monkeypatch):
    websocket, _ = _websocket()

    async def verify(_token):
        await websocket.close()
        return 42, False

    monkeypatch.setattr(module, 'verify_cabinet_ws_token', verify)
    connect = AsyncMock()
    monkeypatch.setattr(module.cabinet_ws_manager, 'connect', connect)

    await module.cabinet_websocket_endpoint(websocket)

    connect.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('error', [WebSocketDisconnect(), OSError('client disconnected')])
async def test_handshake_handles_client_disconnect(monkeypatch, error):
    websocket, _ = _websocket()
    monkeypatch.setattr(websocket, 'accept', AsyncMock(side_effect=error))

    assert await module._accept_websocket(websocket, 'cabinet-auth') is False


@pytest.mark.asyncio
async def test_handshake_does_not_reuse_connection_closed_by_client():
    websocket, send = _websocket()
    await websocket.accept(subprotocol='cabinet-auth')
    websocket.client_state = WebSocketState.DISCONNECTED

    assert await module._accept_websocket(websocket, 'cabinet-auth') is False
    assert send.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('already_accepted', [False, True])
async def test_invalid_credentials_stay_rejected_after_handshake(monkeypatch, already_accepted):
    websocket, send = _websocket()
    if already_accepted:
        await websocket.accept(subprotocol='cabinet-auth')
    monkeypatch.setattr(module, 'verify_cabinet_ws_token', AsyncMock(return_value=(None, False)))
    connect = AsyncMock()
    monkeypatch.setattr(module.cabinet_ws_manager, 'connect', connect)

    await module.cabinet_websocket_endpoint(websocket)

    assert send.await_args.args[0] == {
        'type': 'websocket.close',
        'code': 1008,
        'reason': 'Unauthorized: Invalid token',
    }
    connect.assert_not_awaited()
