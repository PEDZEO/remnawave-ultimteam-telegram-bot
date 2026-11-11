import asyncio
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from app.external.remnawave_api import RemnaWaveAPI, RemnaWaveAPIError


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'error',
    [TimeoutError(), aiohttp.ServerTimeoutError('read timed out'), aiohttp.ClientConnectionError('connection lost')],
)
async def test_transport_errors_use_bounded_retries_and_normalized_exception(monkeypatch, error):
    api = RemnaWaveAPI('https://panel.example', 'test-key')
    api.session = MagicMock()
    api.session.request.side_effect = error
    sleep = AsyncMock()
    monkeypatch.setattr('app.external.remnawave_api.asyncio.sleep', sleep)

    with pytest.raises(RemnaWaveAPIError, match=r'Request failed: .+') as result:
        await api._make_request('GET', '/api/nodes')

    assert result.value.__cause__ is error
    assert api.session.request.call_count == 4
    assert [call.args[0] for call in sleep.await_args_list] == [1.0, 2.0, 4.0]


@pytest.mark.asyncio
async def test_total_timeout_during_response_read_can_recover(monkeypatch):
    api = RemnaWaveAPI('https://panel.example', 'test-key')
    timed_out = MagicMock()
    timed_out.__aenter__ = AsyncMock(return_value=timed_out)
    timed_out.__aexit__ = AsyncMock(return_value=False)
    timed_out.text = AsyncMock(side_effect=TimeoutError())
    recovered = MagicMock(status=200)
    recovered.__aenter__ = AsyncMock(return_value=recovered)
    recovered.__aexit__ = AsyncMock(return_value=False)
    recovered.text = AsyncMock(return_value='{"response": {"nodes": []}}')
    api.session = MagicMock()
    api.session.request.side_effect = [timed_out, recovered]
    monkeypatch.setattr('app.external.remnawave_api.asyncio.sleep', AsyncMock())

    assert await api._make_request('GET', '/api/nodes') == {'response': {'nodes': []}}
    assert api.session.request.call_count == 2


@pytest.mark.asyncio
async def test_cancellation_is_not_retried_or_wrapped(monkeypatch):
    api = RemnaWaveAPI('https://panel.example', 'test-key')
    api.session = MagicMock()
    api.session.request.side_effect = asyncio.CancelledError()
    sleep = AsyncMock()
    monkeypatch.setattr('app.external.remnawave_api.asyncio.sleep', sleep)

    with pytest.raises(asyncio.CancelledError):
        await api._make_request('GET', '/api/nodes')

    assert api.session.request.call_count == 1
    sleep.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('method', ['POST', 'PUT', 'PATCH', 'DELETE'])
async def test_mutations_are_not_repeated_after_an_ambiguous_response_timeout(monkeypatch, method):
    api = RemnaWaveAPI('https://panel.example', 'test-key')
    api.session = MagicMock()
    api.session.request.side_effect = TimeoutError()
    sleep = AsyncMock()
    monkeypatch.setattr('app.external.remnawave_api.asyncio.sleep', sleep)

    with pytest.raises(RemnaWaveAPIError):
        await api._make_request(method, '/api/users')

    assert api.session.request.call_count == 1
    sleep.assert_not_awaited()
