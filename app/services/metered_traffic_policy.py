from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from typing import Any

from app.config import settings


BYTES_PER_GB = 1024**3
MIN_METERED_NODE_MULTIPLIER = 0.1
MAX_METERED_NODE_MULTIPLIER = 100.0


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


def normalize_metered_node_multiplier(value: Any) -> float:
    multiplier = round(float(value), 1)
    if not math.isfinite(multiplier) or not MIN_METERED_NODE_MULTIPLIER <= multiplier <= MAX_METERED_NODE_MULTIPLIER:
        raise ValueError(
            f'Node multiplier must be between {MIN_METERED_NODE_MULTIPLIER:g} and {MAX_METERED_NODE_MULTIPLIER:g}'
        )
    return multiplier


def get_metered_node_multipliers() -> dict[str, float]:
    """Return configured accounting multipliers, falling back to 1x for legacy UUID lists."""
    configured_nodes = get_metered_node_uuids()
    raw_value = str(getattr(settings, 'ULTIMA_METERED_NODE_MULTIPLIERS', '') or '').strip()
    try:
        decoded = json.loads(raw_value) if raw_value else {}
    except (TypeError, ValueError):
        decoded = {}
    if not isinstance(decoded, dict):
        decoded = {}

    result: dict[str, float] = {}
    for node_uuid in configured_nodes:
        try:
            result[node_uuid] = normalize_metered_node_multiplier(decoded.get(node_uuid, 1.0))
        except (TypeError, ValueError):
            result[node_uuid] = 1.0
    return result


def serialize_metered_node_multipliers(values: dict[str, float]) -> str:
    normalized = {
        str(node_uuid): normalize_metered_node_multiplier(multiplier)
        for node_uuid, multiplier in sorted(values.items())
    }
    return json.dumps(normalized, ensure_ascii=True, separators=(',', ':'), sort_keys=True)


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


def get_customer_squad_uuids(active_internal_squads: Any) -> list[str]:
    """Return squads that are selectable and billable for the customer."""
    squads = extract_squad_uuids(active_internal_squads)
    if not is_metered_traffic_enabled():
        return squads

    metered_squad_uuid = get_metered_squad_uuid()
    return [squad_uuid for squad_uuid in squads if squad_uuid != metered_squad_uuid]


def tariff_allows_special_servers(tariff: Any) -> bool:
    """Return whether the tariff explicitly grants access to metered special servers."""
    return bool(tariff and getattr(tariff, 'special_servers_enabled', False))


def tariff_allows_traffic_topup(tariff: Any) -> bool:
    """Return whether buying traffic has an effect for this tariff."""
    if not tariff or not tariff.can_topup_traffic():
        return False
    return not is_metered_traffic_enabled() or tariff_allows_special_servers(tariff)


def subscription_allows_special_servers(subscription: Any, *, tariff: Any | None = None) -> bool:
    if not is_metered_traffic_enabled():
        return False

    resolved_tariff = tariff
    if resolved_tariff is None:
        state = getattr(subscription, '__dict__', {})
        resolved_tariff = state.get('tariff') if isinstance(state, dict) else None
        if resolved_tariff is None and not isinstance(state, dict):
            resolved_tariff = getattr(subscription, 'tariff', None)

    return tariff_allows_special_servers(resolved_tariff)


def build_subscription_squads(
    subscription: Any,
    selected_customer_squads: Any | None = None,
    *,
    tariff: Any | None = None,
) -> list[str]:
    """Build the panel squad list while enforcing tariff-level special-server access."""
    source = (
        getattr(subscription, 'connected_squads', None)
        if selected_customer_squads is None
        else selected_customer_squads
    )
    selected = get_customer_squad_uuids(source)
    if not subscription_allows_special_servers(subscription, tariff=tariff):
        return selected

    limit_gb = max(0, int(getattr(subscription, 'traffic_limit_gb', 0) or 0))
    used_gb = max(0.0, float(getattr(subscription, 'traffic_used_gb', 0.0) or 0.0))
    blocked = bool(getattr(subscription, 'metered_access_blocked', False))
    if blocked or (limit_gb > 0 and used_gb >= limit_gb):
        return selected

    metered_squad_uuid = get_metered_squad_uuid()
    if metered_squad_uuid and metered_squad_uuid not in selected:
        selected.append(metered_squad_uuid)
    return selected


def preserve_metered_squad(active_internal_squads: Any, selected_customer_squads: Any) -> list[str]:
    """Keep the technical squad while replacing the customer-selected squads."""
    selected = get_customer_squad_uuids(selected_customer_squads)
    metered_squad_uuid = get_metered_squad_uuid()
    current = extract_squad_uuids(active_internal_squads)
    if is_metered_traffic_enabled() and metered_squad_uuid in current and metered_squad_uuid not in selected:
        selected.append(metered_squad_uuid)
    return selected


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


def reset_metered_cycle(
    subscription: Any,
    *,
    panel_counter_bytes: int = 0,
    tariff: Any | None = None,
) -> None:
    if not is_metered_traffic_enabled():
        return

    now = datetime.now(UTC)
    counter = max(0, int(panel_counter_bytes or 0))
    subscription.metered_traffic_baseline_bytes = counter
    subscription.metered_traffic_last_counter_bytes = counter
    subscription.metered_traffic_initialized_at = now
    subscription.metered_traffic_last_checked_at = now
    subscription.metered_access_blocked = False
    subscription.metered_access_blocked_at = None
    subscription.metered_warning_percent = 0
    subscription.traffic_used_gb = 0.0

    subscription.connected_squads = build_subscription_squads(subscription, tariff=tariff)


def disable_metered_access(subscription: Any, *, panel_counter_bytes: int | None = None) -> bool:
    """Remove only the technical squad and clear stale metered state."""
    before = extract_squad_uuids(getattr(subscription, 'connected_squads', None))
    _remove_squad(subscription, get_metered_squad_uuid())
    after = extract_squad_uuids(getattr(subscription, 'connected_squads', None))

    if panel_counter_bytes is not None:
        counter = max(0, int(panel_counter_bytes or 0))
        subscription.metered_traffic_baseline_bytes = counter
        subscription.metered_traffic_last_counter_bytes = counter
        subscription.metered_traffic_initialized_at = datetime.now(UTC)
        subscription.metered_traffic_last_checked_at = datetime.now(UTC)

    subscription.traffic_used_gb = 0.0
    subscription.metered_access_blocked = False
    subscription.metered_access_blocked_at = None
    subscription.metered_warning_percent = 0
    return before != after


def restore_metered_access_if_available(subscription: Any) -> bool:
    if not is_metered_traffic_enabled():
        return False

    if not subscription_allows_special_servers(subscription):
        return disable_metered_access(subscription)

    limit_gb = max(0, int(getattr(subscription, 'traffic_limit_gb', 0) or 0))
    used_gb = max(0.0, float(getattr(subscription, 'traffic_used_gb', 0.0) or 0.0))
    if limit_gb > 0 and used_gb >= limit_gb:
        return False

    metered_squad_uuid = get_metered_squad_uuid()
    current_squads = extract_squad_uuids(getattr(subscription, 'connected_squads', None))
    was_blocked = bool(getattr(subscription, 'metered_access_blocked', False))
    was_missing = metered_squad_uuid not in current_squads
    _add_squad(subscription, metered_squad_uuid)
    subscription.metered_access_blocked = False
    subscription.metered_access_blocked_at = None
    subscription.metered_warning_percent = 0
    return was_blocked or was_missing


def block_metered_access(subscription: Any) -> None:
    squad_uuid = get_metered_squad_uuid()
    _remove_squad(subscription, squad_uuid)
    subscription.metered_access_blocked = True
    subscription.metered_access_blocked_at = datetime.now(UTC)
    subscription.metered_warning_percent = 100
