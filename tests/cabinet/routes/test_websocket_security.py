from types import SimpleNamespace
from typing import cast

from fastapi import WebSocket
from starlette.datastructures import Headers, QueryParams

from app.cabinet.routes.websocket import _get_websocket_credentials


def _websocket(*, protocols: str = '', query: str = '') -> WebSocket:
    return cast(
        'WebSocket',
        SimpleNamespace(
            headers=Headers({'sec-websocket-protocol': protocols}),
            query_params=QueryParams(query),
        ),
    )


def test_websocket_credentials_prefer_subprotocol_over_query_token() -> None:
    token, subprotocol = _get_websocket_credentials(
        _websocket(protocols='cabinet-auth, current-token', query='token=legacy-token')
    )

    assert token == 'current-token'
    assert subprotocol == 'cabinet-auth'


def test_websocket_credentials_keep_legacy_query_compatibility() -> None:
    token, subprotocol = _get_websocket_credentials(_websocket(query='token=legacy-token'))

    assert token == 'legacy-token'
    assert subprotocol is None
