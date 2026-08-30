from unittest.mock import AsyncMock

import pytest

from app.cabinet.routes import admin_balancer


pytestmark = pytest.mark.asyncio


async def test_get_attack_mode_uses_protected_admin_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    proxy = AsyncMock(return_value={'status': 'ok', 'nodes': []})
    monkeypatch.setattr(admin_balancer, '_proxy_balancer_json', proxy)

    result = await admin_balancer.get_balancer_attack_mode(admin=None)  # type: ignore[arg-type]

    assert result == {'status': 'ok', 'nodes': []}
    proxy.assert_awaited_once_with('GET', '/admin/attack-mode', requires_admin=True)


async def test_get_hosts_uses_protected_admin_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    proxy = AsyncMock(return_value={'status': 'ok', 'hosts': []})
    monkeypatch.setattr(admin_balancer, '_proxy_balancer_json', proxy)

    result = await admin_balancer.get_balancer_hosts(admin=None)  # type: ignore[arg-type]

    assert result == {'status': 'ok', 'hosts': []}
    proxy.assert_awaited_once_with('GET', '/admin/hosts', requires_admin=True)


async def test_get_health_metrics_uses_protected_admin_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proxy = AsyncMock(return_value={'node-a': {'lastRttMs': 25, 'lossPercent': 0}})
    monkeypatch.setattr(admin_balancer, '_proxy_balancer_json', proxy)

    result = await admin_balancer.get_balancer_health_metrics(admin=None)  # type: ignore[arg-type]

    assert result == {'node-a': {'lastRttMs': 25, 'lossPercent': 0}}
    proxy.assert_awaited_once_with('GET', '/admin/health-metrics', requires_admin=True)


async def test_enable_attack_mode_forwards_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    proxy = AsyncMock(return_value={'status': 'ok'})
    monkeypatch.setattr(admin_balancer, '_proxy_balancer_json', proxy)
    payload = {'node': 'DE Main', 'ttl_sec': 300, 'reason': 'manual_ddos'}

    await admin_balancer.enable_balancer_attack_mode(payload, admin=None)  # type: ignore[arg-type]

    proxy.assert_awaited_once_with(
        'POST',
        '/admin/attack-mode',
        requires_admin=True,
        json_body=payload,
    )


async def test_disable_attack_mode_quotes_node_name(monkeypatch: pytest.MonkeyPatch) -> None:
    proxy = AsyncMock(return_value={'status': 'ok', 'released': True})
    monkeypatch.setattr(admin_balancer, '_proxy_balancer_json', proxy)

    await admin_balancer.disable_balancer_attack_mode('DE Main/1', admin=None)  # type: ignore[arg-type]

    proxy.assert_awaited_once_with(
        'DELETE',
        '/admin/attack-mode/DE%20Main%2F1',
        requires_admin=True,
    )


@pytest.mark.parametrize(
    ('handler', 'path'),
    [
        (admin_balancer.refresh_balancer_groups, '/admin/refresh-groups'),
        (admin_balancer.refresh_balancer_stats, '/admin/refresh-stats'),
    ],
)
async def test_refresh_actions_use_post(
    monkeypatch: pytest.MonkeyPatch,
    handler: object,
    path: str,
) -> None:
    proxy = AsyncMock(return_value={'status': 'ok'})
    monkeypatch.setattr(admin_balancer, '_proxy_balancer_json', proxy)

    await handler(admin=None)  # type: ignore[operator]

    proxy.assert_awaited_once_with('POST', path, requires_admin=True)
