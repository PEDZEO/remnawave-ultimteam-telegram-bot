from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import permission_service
from app.services.permission_service import PermissionService


pytestmark = pytest.mark.asyncio


def _policy(
    policy_id: int,
    *,
    effect: str = 'allow',
    conditions: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=policy_id,
        name=f'policy-{policy_id}',
        effect=effect,
        conditions=conditions or {},
        resource='users',
        actions=['read'],
    )


async def _check(monkeypatch: pytest.MonkeyPatch, policies: list[SimpleNamespace], ip: str) -> tuple[bool, str]:
    monkeypatch.setattr(permission_service, '_is_legacy_admin', lambda _user: False)
    monkeypatch.setattr(
        permission_service.UserRoleCRUD,
        'get_user_permissions',
        AsyncMock(return_value=(['users:read'], ['operator'], 10)),
    )
    monkeypatch.setattr(
        permission_service.UserRoleCRUD,
        'get_user_roles',
        AsyncMock(return_value=[SimpleNamespace(role_id=1)]),
    )
    monkeypatch.setattr(
        permission_service.AccessPolicyCRUD,
        'get_policies_for_user',
        AsyncMock(return_value=policies),
    )
    return await PermissionService.check_permission(
        SimpleNamespace(),
        SimpleNamespace(id=7),
        'users:read',
        ip_address=ip,
    )


async def test_allow_ip_whitelist_denies_non_matching_address(monkeypatch: pytest.MonkeyPatch) -> None:
    allowed, reason = await _check(
        monkeypatch,
        [_policy(1, conditions={'ip_whitelist': ['10.10.0.0/16']})],
        '203.0.113.7',
    )

    assert allowed is False
    assert reason == 'No allow policy conditions matched'


async def test_allow_ip_whitelist_accepts_matching_address(monkeypatch: pytest.MonkeyPatch) -> None:
    allowed, _ = await _check(
        monkeypatch,
        [_policy(1, conditions={'ip_whitelist': ['10.10.0.0/16']})],
        '10.10.20.30',
    )

    assert allowed is True


async def test_matching_deny_policy_overrides_allow(monkeypatch: pytest.MonkeyPatch) -> None:
    policies = [
        _policy(1),
        _policy(2, effect='deny', conditions={'ip_whitelist': ['203.0.113.0/24']}),
    ]

    allowed, reason = await _check(monkeypatch, policies, '203.0.113.7')

    assert allowed is False
    assert reason == 'Denied by policy: policy-2'


async def test_max_actions_per_hour_is_enforced_atomically(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = AsyncMock(side_effect=[False, True])
    monkeypatch.setattr(permission_service.RateLimitCache, 'is_rate_limited', limiter)
    policies = [_policy(1, conditions={'max_actions_per_hour': 1})]

    first, _ = await _check(monkeypatch, policies, '203.0.113.7')
    second, reason = await _check(monkeypatch, policies, '203.0.113.7')

    assert first is True
    assert second is False
    assert reason == 'No allow policy conditions matched'
    limiter.assert_awaited_with(7, 'abac:1:users:read', 1, 3600, fail_closed=True)
