from datetime import UTC, datetime
from typing import Any, Self

import pytest

from app.config import settings
from app.external.remnawave_api import RemnaWaveAPI, RemnaWaveAPIError, TrafficLimitStrategy, UserStatus


@pytest.mark.asyncio
async def test_get_user_by_uuid_treats_not_found_as_expected(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    calls: list[tuple[str, str, tuple[int, ...]]] = []

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        calls.append((method, endpoint, quiet_statuses))
        raise RemnaWaveAPIError('User with specified params not found', status_code=404)

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    assert await api.get_user_by_uuid('missing-user') is None
    assert calls == [('GET', '/api/users/missing-user', (404,))]


@pytest.mark.asyncio
async def test_happ_crypto_link_uses_v5_service_without_panel_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    calls: list[dict[str, Any]] = []

    class FakeResponse:
        status = 200

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def json(self, **_kwargs: Any) -> dict[str, str]:
            return {'encrypted_link': 'happ://crypt5/generated'}

    class FakeSession:
        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        def post(self, url: str, **kwargs: Any) -> FakeResponse:
            calls.append({'url': url, **kwargs})
            return FakeResponse()

    monkeypatch.setattr(
        'app.external.remnawave_api.aiohttp.ClientSession',
        lambda **_kwargs: FakeSession(),
    )

    link = await api.encrypt_happ_crypto_link('https://sub.example/api/sub/abc')

    assert link == 'happ://crypt5/generated'
    assert calls == [
        {
            'url': 'https://crypto.happ.su/api-v2.php',
            'json': {'url': 'https://sub.example/api/sub/abc'},
            'headers': {'Accept': 'application/json'},
        }
    ]
    assert all('Authorization' not in call.get('headers', {}) for call in calls)


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
async def test_update_node_multipliers_uses_bulk_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
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

    assert await api.update_nodes_consumption_multiplier(['node-1', 'node-1', 'node-2'], 1) is True
    assert calls == [
        (
            'POST',
            '/api/nodes/bulk-actions/update',
            {
                'uuids': ['node-1', 'node-2'],
                'fields': {'consumptionMultiplier': 1.0},
            },
        )
    ]


@pytest.mark.asyncio
async def test_update_node_multipliers_falls_back_to_patch(monkeypatch: pytest.MonkeyPatch) -> None:
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
        if endpoint == '/api/nodes/bulk-actions/update':
            raise RemnaWaveAPIError('Not found', status_code=404)
        return {'response': {}}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    assert await api.update_nodes_consumption_multiplier(['node-1', 'node-2'], 0) is True
    assert calls == [
        (
            'POST',
            '/api/nodes/bulk-actions/update',
            {
                'uuids': ['node-1', 'node-2'],
                'fields': {'consumptionMultiplier': 0.0},
            },
        ),
        ('PATCH', '/api/nodes', {'uuid': 'node-1', 'consumptionMultiplier': 0.0}),
        ('PATCH', '/api/nodes', {'uuid': 'node-2', 'consumptionMultiplier': 0.0}),
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


@pytest.mark.asyncio
async def test_get_bandwidth_stats_nodes_users_sends_required_date_range(
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
        assert data == {'nodesUuids': ['node-1']}
        assert params == {'start': '2026-07-01', 'end': '2026-07-16'}
        return {'response': {'categories': [], 'sparklineData': [], 'topUsers': []}}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    await api.get_bandwidth_stats_nodes_users(
        ['node-1'],
        start_date='2026-07-01',
        end_date='2026-07-16',
    )


@pytest.mark.asyncio
async def test_metered_mode_forces_unlimited_no_reset_panel_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, 'ULTIMA_METERED_TRAFFIC_ENABLED', True)
    monkeypatch.setattr(settings, 'ULTIMA_METERED_SQUAD_UUID', '11111111-1111-1111-1111-111111111111')
    monkeypatch.setattr(settings, 'ULTIMA_METERED_NODE_UUIDS', '22222222-2222-2222-2222-222222222222')
    api = RemnaWaveAPI('https://panel.example', 'token')
    now = datetime(2026, 7, 16, tzinfo=UTC)
    payloads: list[dict[str, Any]] = []

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        assert method in {'POST', 'PATCH'}
        payloads.append(data or {})
        return {
            'response': {
                'uuid': 'user-uuid',
                'shortUuid': 'short',
                'username': 'demo',
                'status': 'ACTIVE',
                'trafficLimitBytes': 0,
                'trafficLimitStrategy': 'NO_RESET',
                'expireAt': now.isoformat(),
                'subscriptionUrl': '',
                'activeInternalSquads': [],
                'createdAt': now.isoformat(),
                'updatedAt': now.isoformat(),
            }
        }

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    await api.create_user(
        username='demo',
        expire_at=now,
        status=UserStatus.ACTIVE,
        traffic_limit_bytes=35 * 1024**3,
        traffic_limit_strategy=TrafficLimitStrategy.MONTH,
    )
    await api.update_user(
        uuid='user-uuid',
        traffic_limit_bytes=40 * 1024**3,
        traffic_limit_strategy=TrafficLimitStrategy.MONTH,
    )

    assert [payload['trafficLimitBytes'] for payload in payloads] == [0, 0]
    assert [payload['trafficLimitStrategy'] for payload in payloads] == ['NO_RESET', 'NO_RESET']


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


@pytest.mark.parametrize('raw_status', [None, 'FUTURE_PANEL_STATUS'])
def test_parse_user_fails_closed_for_unknown_status(raw_status: str | None) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    now = datetime(2026, 7, 5, tzinfo=UTC).isoformat()

    user = api._parse_user(
        {
            'uuid': 'user-uuid',
            'shortUuid': 'short',
            'username': 'demo',
            'status': raw_status,
            'trafficLimitBytes': 0,
            'trafficLimitStrategy': 'NO_RESET',
            'expireAt': now,
            'createdAt': now,
            'updatedAt': now,
        }
    )

    assert user.status.value == 'DISABLED'
