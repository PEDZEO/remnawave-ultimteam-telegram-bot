from datetime import UTC, datetime
from typing import Any, Self

import pytest

from app.config import settings
from app.external.remnawave_api import RemnaWaveAPI, RemnaWaveAPIError, TrafficLimitStrategy, UserStatus


def _user_payload(*, uuid: str | None = None, user_id: int | None = None) -> dict[str, Any]:
    now = datetime(2026, 8, 3, tzinfo=UTC).isoformat()
    payload: dict[str, Any] = {
        'shortUuid': 'short',
        'username': 'demo',
        'status': 'ACTIVE',
        'trafficLimitBytes': 0,
        'trafficLimitStrategy': 'NO_RESET',
        'expireAt': now,
        'createdAt': now,
        'updatedAt': now,
    }
    if uuid is not None:
        payload['uuid'] = uuid
    if user_id is not None:
        payload['id'] = user_id
    return payload


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
    assert calls == [('GET', '/api/users/missing-user', (400, 404))]


def test_parse_v3_user_uses_numeric_id_as_compatibility_identifier() -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')

    user = api._parse_user(_user_payload(user_id=42))

    assert user.uuid == '42'
    assert user.id == 42


@pytest.mark.asyncio
async def test_update_user_selects_identifier_for_each_panel_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    payloads: list[dict[str, Any]] = []

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        assert method == 'PATCH'
        assert endpoint == '/api/users'
        payloads.append(data or {})
        response_user = _user_payload(user_id=data['id']) if data and 'id' in data else _user_payload(uuid=data['uuid'])
        return {'response': response_user}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    await api.update_user('42', description='v3')
    await api.update_user('11111111-1111-1111-1111-111111111111', description='v2')

    assert payloads[0]['id'] == 42
    assert 'uuid' not in payloads[0]
    assert payloads[1]['uuid'] == '11111111-1111-1111-1111-111111111111'
    assert 'id' not in payloads[1]


@pytest.mark.asyncio
async def test_get_user_by_id_falls_back_to_v2_route(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    calls: list[str] = []

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        calls.append(endpoint)
        if endpoint == '/api/users/42':
            raise RemnaWaveAPIError('Invalid UUID', status_code=400)
        return {'response': _user_payload(uuid='11111111-1111-1111-1111-111111111111')}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    user = await api.get_user_by_id(42)

    assert user is not None
    assert user.uuid == '11111111-1111-1111-1111-111111111111'
    assert calls == ['/api/users/42', '/api/users/by-id/42']


@pytest.mark.asyncio
async def test_removed_lookup_routes_fall_back_to_v3_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    stream_params: list[dict[str, Any]] = []

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        if endpoint.startswith('/api/users/by-'):
            raise RemnaWaveAPIError('Route not found', status_code=404)
        assert endpoint == '/api/users/stream'
        stream_params.append(params or {})
        return {'response': {'users': [_user_payload(user_id=42)], 'nextCursor': None, 'hasMore': False}}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    telegram_users = await api.get_user_by_telegram_id(12345)
    email_users = await api.get_user_by_email('user@example.com')

    assert [user.uuid for user in telegram_users] == ['42']
    assert [user.uuid for user in email_users] == ['42']
    assert stream_params == [
        {'size': 100, 'telegramId': 12345},
        {'size': 100, 'email': 'user@example.com'},
    ]


@pytest.mark.asyncio
async def test_missing_v2_lookup_stays_empty_when_stream_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        raise RemnaWaveAPIError('Not found', status_code=404)

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    assert await api.get_user_by_telegram_id(12345) == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('response', 'expected'),
    [({}, True), ({'response': True}, True), ({'response': {'isDeleted': False}}, False)],
)
async def test_delete_user_accepts_v2_and_v3_response_shapes(
    monkeypatch: pytest.MonkeyPatch,
    response: dict[str, Any],
    expected: bool,
) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')

    async def fake_make_request(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return response

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    assert await api.delete_user('42') is expected


@pytest.mark.asyncio
async def test_hwid_delete_uses_user_id_on_v3_and_uuid_on_v2(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    payloads: list[dict[str, Any]] = []

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        payloads.append(data or {})
        return {'response': {'total': 0, 'devices': []}}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    assert await api.remove_device('42', 'device-1') is True
    assert await api.remove_device('11111111-1111-1111-1111-111111111111', 'device-2') is True
    assert payloads == [
        {'userId': 42, 'hwid': 'device-1'},
        {'userUuid': '11111111-1111-1111-1111-111111111111', 'hwid': 'device-2'},
    ]


@pytest.mark.asyncio
async def test_v3_bulk_node_usage_normalizes_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        assert method == 'POST'
        assert endpoint == '/api/bandwidth-stats/nodes/usage'
        assert data == {'nodesUuids': ['node-1', 'node-2']}
        assert params == {'start': '2026-08-01', 'end': '2026-08-03', 'minTotalBytes': 0}
        assert quiet_statuses == (404, 405)
        return {'response': {'nodes': []}}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    assert await api.get_bandwidth_stats_nodes_usage(
        ['node-1', 'node-1', 'node-2'],
        '2026-08-01T00:00:00Z',
        '2026-08-03T23:59:59Z',
    ) == {'nodes': []}


@pytest.mark.asyncio
async def test_legacy_node_usage_falls_back_to_v3_bulk_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    calls: list[str] = []

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        calls.append(endpoint)
        if endpoint.endswith('/legacy'):
            raise RemnaWaveAPIError('Not found', status_code=404)
        return {
            'response': {
                'nodes': [
                    {
                        'uuid': 'node-1',
                        'users': [{'id': 42, 'totalBytes': 1234}],
                    }
                ]
            }
        }

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    usage = await api.get_bandwidth_stats_node_users_legacy('node-1', '2026-08-01', '2026-08-03')

    assert usage == [
        {
            'userUuid': '42',
            'username': '',
            'nodeUuid': 'node-1',
            'total': 1234,
        }
    ]
    assert calls == [
        '/api/bandwidth-stats/nodes/node-1/users/legacy',
        '/api/bandwidth-stats/nodes/usage',
    ]


@pytest.mark.asyncio
async def test_get_all_users_complete_uses_bounded_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    calls: list[tuple[int, int]] = []
    first_page = [object(), object()]
    second_page = [object()]

    async def fake_get_all_users(start: int, size: int, enrich_happ_links: bool = False) -> dict[str, Any]:
        calls.append((start, size))
        return {'users': first_page if start == 0 else second_page, 'total': 3}

    monkeypatch.setattr(api, 'get_all_users', fake_get_all_users)

    users = await api.get_all_users_complete(page_size=2)

    assert users == first_page + second_page
    assert calls == [(0, 2), (2, 2)]


def test_parse_node_supports_nested_v3_system_and_versions() -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    now = datetime(2026, 8, 3, tzinfo=UTC).isoformat()

    node = api._parse_node(
        {
            'uuid': '11111111-1111-1111-1111-111111111111',
            'name': 'node',
            'address': '127.0.0.1',
            'countryCode': 'NL',
            'isConnected': True,
            'isDisabled': False,
            'xrayUptime': 123,
            'versions': {'xray': '25.8.3', 'node': '3.0.0'},
            'system': {
                'info': {
                    'cpus': 4,
                    'cpuModel': 'Example CPU',
                    'memoryTotal': 8 * 1024**3,
                }
            },
            'createdAt': now,
            'updatedAt': now,
        }
    )

    assert node.xray_version == '25.8.3'
    assert node.node_version == '3.0.0'
    assert node.cpu_count == 4
    assert node.cpu_model == 'Example CPU'
    assert node.total_ram == 8 * 1024**3
    assert node.xray_uptime == 123


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
async def test_v3_empty_async_action_responses_are_successful(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        return {}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    assert await api.restart_node('node-uuid') is True
    assert await api.restart_all_nodes() is True
    assert await api.add_users_to_internal_squad('squad-uuid') is True
    assert await api.remove_users_from_internal_squad('squad-uuid') is True
    assert await api.add_users_to_external_squad('squad-uuid') is True
    assert await api.remove_users_from_external_squad('squad-uuid') is True


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
