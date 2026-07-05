import base64
from datetime import UTC, datetime
from typing import Any

import pytest

from app.external.remnawave_api import RemnaWaveAPI, RemnaWaveAPIError, TrafficLimitStrategy


@pytest.mark.asyncio
async def test_happ_crypto_link_is_generated_locally(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')

    async def fail_make_request(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise AssertionError('Remnawave Happ encrypt endpoint must not be called')

    monkeypatch.setattr(api, '_make_request', fail_make_request)

    link = await api.encrypt_happ_crypto_link('https://sub.example/api/sub/abc')

    assert link is not None
    assert link.startswith('happ://crypt4/')
    base64.b64decode(link.removeprefix('happ://crypt4/'), validate=True)


@pytest.mark.asyncio
async def test_restart_node_sends_required_force_restart_body(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        calls.append((method, endpoint, data))
        return {'response': {'eventSent': True}}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    assert await api.restart_node('node-uuid', force_restart=True) is True
    assert calls == [('POST', '/api/nodes/node-uuid/actions/restart', {'forceRestart': True})]


@pytest.mark.asyncio
async def test_remove_users_from_squad_falls_back_to_legacy_post(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    calls: list[tuple[str, str]] = []

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        calls.append((method, endpoint))
        if method == 'DELETE':
            raise RemnaWaveAPIError('Method not allowed', status_code=405)
        return {'response': {'eventSent': True}}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    assert await api.remove_users_from_internal_squad('squad-uuid') is True
    assert calls == [
        ('DELETE', '/api/internal-squads/squad-uuid/bulk-actions/remove-users'),
        ('POST', '/api/internal-squads/squad-uuid/bulk-actions/remove-users'),
    ]


@pytest.mark.asyncio
async def test_get_bandwidth_stats_nodes_users_uses_new_multi_node_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        assert method == 'POST'
        assert endpoint == '/api/bandwidth-stats/nodes/users'
        assert data == {'nodesUuids': ['node-1', 'node-2']}
        return {'response': {'categories': ['now'], 'sparklineData': [1], 'topUsers': []}}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    assert await api.get_bandwidth_stats_nodes_users(['node-1', 'node-2']) == {
        'categories': ['now'],
        'sparklineData': [1],
        'topUsers': [],
    }


def test_parse_user_accepts_month_rolling_and_number_traffic() -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    now = datetime(2026, 7, 5, tzinfo=UTC).isoformat()

    user = api._parse_user(
        {
            'uuid': 'user-uuid',
            'id': 42,
            'shortUuid': 'short',
            'username': 'demo',
            'status': 'ACTIVE',
            'trafficLimitBytes': 123.9,
            'trafficLimitStrategy': 'MONTH_ROLLING',
            'expireAt': now,
            'telegramId': None,
            'email': None,
            'hwidDeviceLimit': None,
            'description': None,
            'tag': None,
            'subscriptionUrl': 'https://sub.example/api/sub/short',
            'activeInternalSquads': [],
            'createdAt': now,
            'updatedAt': now,
            'userTraffic': {
                'usedTrafficBytes': 10.9,
                'lifetimeUsedTrafficBytes': 20.1,
                'onlineAt': None,
                'firstConnectedAt': None,
                'lastConnectedNodeUuid': None,
            },
        }
    )

    assert user.traffic_limit_strategy is TrafficLimitStrategy.MONTH_ROLLING
    assert user.traffic_limit_bytes == 123
    assert user.used_traffic_bytes == 10
    assert user.lifetime_used_traffic_bytes == 20
