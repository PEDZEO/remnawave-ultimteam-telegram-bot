from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.config import settings


BYTES_PER_GB = 1024**3


def is_metered_traffic_enabled() -> bool:
    return bool(
        getattr(settings, 'ULTIMA_METERED_TRAFFIC_ENABLED', False)
        and get_metered_squad_uuid()
        and get_metered_node_uuids()
    )


def get_metered_squad_uuid() -> str:
    return str(getattr(settings, 'ULTIMA_METERED_SQUAD_UUID', '') or '').strip()


def get_metered_node_uuids() -> list[str]:
    raw_value = str(getattr(settings, 'ULTIMA_METERED_NODE_UUIDS', '') or '')
    return list(dict.fromkeys(part.strip() for part in raw_value.split(',') if part.strip()))


def get_metered_check_interval_seconds() -> int:
    raw_value = int(getattr(settings, 'ULTIMA_METERED_CHECK_INTERVAL_SECONDS', 60) or 60)
    return min(3600, max(15, raw_value))


def get_metered_warning_percent() -> int:
    raw_value = int(getattr(settings, 'ULTIMA_METERED_WARNING_PERCENT', 80) or 80)
    return min(95, max(25, raw_value))


def panel_traffic_limit_bytes(traffic_limit_gb: float | None) -> int:
    if is_metered_traffic_enabled():
        return 0
    value = max(0, int(traffic_limit_gb or 0))
    return value * BYTES_PER_GB


def extract_squad_uuids(active_internal_squads: Any) -> list[str]:
    if not isinstance(active_internal_squads, list):
        return []

    result: list[str] = []
    for item in active_internal_squads:
        if isinstance(item, str):
            squad_uuid = item.strip()
        elif isinstance(item, dict):
            squad_uuid = str(item.get('uuid') or '').strip()
        else:
            squad_uuid = ''
        if squad_uuid and squad_uuid not in result:
            result.append(squad_uuid)
    return result


def calculate_metered_usage(
    *,
    panel_counter_bytes: int,
    baseline_bytes: int,
    last_counter_bytes: int,
) -> tuple[int, int, bool]:
    current = max(0, int(panel_counter_bytes or 0))
    baseline = max(0, int(baseline_bytes or 0))
    previous = max(0, int(last_counter_bytes or 0))

    counter_was_reset = current < previous or current < baseline
    if counter_was_reset:
        baseline = 0

    return max(0, current - baseline), baseline, counter_was_reset


def _add_squad(subscription: Any, squad_uuid: str) -> None:
    squads = extract_squad_uuids(getattr(subscription, 'connected_squads', None))
    if squad_uuid and squad_uuid not in squads:
        squads.append(squad_uuid)
    subscription.connected_squads = squads


def _remove_squad(subscription: Any, squad_uuid: str) -> None:
    subscription.connected_squads = [
        item for item in extract_squad_uuids(getattr(subscription, 'connected_squads', None)) if item != squad_uuid
    ]


def reset_metered_cycle(subscription: Any, *, panel_counter_bytes: int = 0) -> None:
    if not is_metered_traffic_enabled():
        return

    now = datetime.now(UTC)
    counter = max(0, int(panel_counter_bytes or 0))
    was_blocked = bool(getattr(subscription, 'metered_access_blocked', False))
    subscription.metered_traffic_baseline_bytes = counter
    subscription.metered_traffic_last_counter_bytes = counter
    subscription.metered_traffic_initialized_at = now
    subscription.metered_traffic_last_checked_at = now
    subscription.metered_access_blocked = False
    subscription.metered_access_blocked_at = None
    subscription.metered_warning_percent = 0
    subscription.traffic_used_gb = 0.0

    if was_blocked:
        _add_squad(subscription, get_metered_squad_uuid())


def restore_metered_access_if_available(subscription: Any) -> bool:
    if not is_metered_traffic_enabled() or not getattr(subscription, 'metered_access_blocked', False):
        return False

    limit_gb = max(0, int(getattr(subscription, 'traffic_limit_gb', 0) or 0))
    used_gb = max(0.0, float(getattr(subscription, 'traffic_used_gb', 0.0) or 0.0))
    if limit_gb > 0 and used_gb >= limit_gb:
        return False

    _add_squad(subscription, get_metered_squad_uuid())
    subscription.metered_access_blocked = False
    subscription.metered_access_blocked_at = None
    subscription.metered_warning_percent = 0
    return True


def block_metered_access(subscription: Any) -> None:
    squad_uuid = get_metered_squad_uuid()
    _remove_squad(subscription, squad_uuid)
    subscription.metered_access_blocked = True
    subscription.metered_access_blocked_at = datetime.now(UTC)
    subscription.metered_warning_percent = 100
