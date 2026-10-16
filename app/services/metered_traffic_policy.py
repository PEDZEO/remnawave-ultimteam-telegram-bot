from __future__ import annotations

import json
import math
from calendar import monthrange
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.config import settings


BYTES_PER_GB = 1024**3
METERED_TRAFFIC_TIMEZONE = 'Europe/Moscow'
MIN_METERED_NODE_MULTIPLIER = 0.1
MAX_METERED_NODE_MULTIPLIER = 100.0


def is_metered_traffic_enabled() -> bool:
    return bool(
        getattr(settings, 'ULTIMA_METERED_TRAFFIC_ENABLED', False)
        and get_metered_squad_uuids()
        and get_metered_node_uuids()
    )


def get_metered_squad_uuids() -> list[str]:
    """Return all technical squads, including legacy single-value configuration."""
    raw_value = str(getattr(settings, 'ULTIMA_METERED_SQUAD_UUID', '') or '')
    return list(dict.fromkeys(part.strip() for part in raw_value.split(',') if part.strip()))


def get_metered_squad_uuid() -> str:
    """Return the first technical squad for compatibility with older integrations."""
    squad_uuids = get_metered_squad_uuids()
    return squad_uuids[0] if squad_uuids else ''


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

    metered_squad_uuids = set(get_metered_squad_uuids())
    return [squad_uuid for squad_uuid in squads if squad_uuid not in metered_squad_uuids]


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

    for metered_squad_uuid in get_metered_squad_uuids():
        if metered_squad_uuid not in selected:
            selected.append(metered_squad_uuid)
    return selected


def preserve_metered_squad(active_internal_squads: Any, selected_customer_squads: Any) -> list[str]:
    """Keep the technical squad while replacing the customer-selected squads."""
    selected = get_customer_squad_uuids(selected_customer_squads)
    current = extract_squad_uuids(active_internal_squads)
    if is_metered_traffic_enabled():
        for metered_squad_uuid in get_metered_squad_uuids():
            if metered_squad_uuid in current and metered_squad_uuid not in selected:
                selected.append(metered_squad_uuid)
    return selected


def calculate_metered_usage(
    *,
    panel_counter_bytes: int,
    baseline_bytes: int,
    last_counter_bytes: int,
    counter_reset_detected: bool = False,
) -> tuple[int, int, bool]:
    current = max(0, int(panel_counter_bytes or 0))
    baseline = int(baseline_bytes or 0)
    previous = max(0, int(last_counter_bytes or 0))

    counter_was_reset = counter_reset_detected or current < previous or current < baseline
    if counter_was_reset:
        # Keep usage already accounted in this billing period when the panel
        # restarts its counter. Only our scheduled/manual reset grants new quota.
        baseline = -max(0, previous - baseline)

    return max(0, current - baseline), baseline, counter_was_reset


def get_metered_traffic_period(
    subscription: Any,
    *,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Return monthly connection anniversaries without drifting after short months."""
    current = now or datetime.now(UTC)
    timezone = ZoneInfo(METERED_TRAFFIC_TIMEZONE)
    anchor = (
        getattr(subscription, 'start_date', None)
        or getattr(subscription, 'created_at', None)
        or getattr(subscription, 'metered_traffic_initialized_at', None)
        or current
    )
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=UTC)
    anchor = anchor.astimezone(timezone)
    local_now = current.astimezone(timezone)
    months = max(0, (local_now.year - anchor.year) * 12 + local_now.month - anchor.month)

    def anniversary(offset: int) -> datetime:
        year, month_index = divmod(anchor.year * 12 + anchor.month - 1 + offset, 12)
        month = month_index + 1
        return anchor.replace(year=year, month=month, day=min(anchor.day, monthrange(year, month)[1]))

    if months > 0 and anniversary(months) > local_now:
        months -= 1
    return anniversary(months).astimezone(UTC), anniversary(months + 1).astimezone(UTC)


def metered_cycle_is_due(subscription: Any, *, now: datetime | None = None) -> bool:
    initialized_at = getattr(subscription, 'metered_traffic_initialized_at', None)
    if initialized_at is None:
        return False
    if initialized_at.tzinfo is None:
        initialized_at = initialized_at.replace(tzinfo=UTC)
    current = now or datetime.now(UTC)
    period_start, _ = get_metered_traffic_period(subscription, now=current)
    return initialized_at < period_start <= current


def refresh_metered_usage(
    subscription: Any,
    *,
    panel_counter_bytes: int,
    now: datetime,
    panel_reset_at: datetime | None = None,
    sampled_at: datetime | None = None,
) -> tuple[int, bool, bool]:
    """Advance the monthly cycle and account a panel sample; never create usage debt."""
    counter = max(0, int(panel_counter_bytes or 0))
    initialized = getattr(subscription, 'metered_traffic_initialized_at', None) is None
    renewed = not initialized and metered_cycle_is_due(subscription, now=now)
    if initialized or renewed:
        baseline = counter
        used_bytes = 0
        subscription.metered_traffic_initialized_at = now
        subscription.metered_warning_percent = 0
    elif getattr(subscription, 'metered_access_blocked', False):
        # Connections may keep reporting bytes after the squad has been removed.
        # Those bytes must not consume the next purchased package.
        used_bytes = round(max(0.0, float(subscription.traffic_used_gb or 0.0)) * BYTES_PER_GB)
        limit_bytes = max(0, int(subscription.traffic_limit_gb or 0)) * BYTES_PER_GB
        if limit_bytes > 0:
            used_bytes = min(used_bytes, limit_bytes)
        baseline = counter - used_bytes
    else:
        last_checked = getattr(subscription, 'metered_traffic_last_checked_at', None)
        reset_detected = bool(panel_reset_at and last_checked and last_checked < panel_reset_at <= now)
        used_bytes, baseline, _ = calculate_metered_usage(
            panel_counter_bytes=counter,
            baseline_bytes=subscription.metered_traffic_baseline_bytes,
            last_counter_bytes=subscription.metered_traffic_last_counter_bytes,
            counter_reset_detected=reset_detected,
        )
        limit_bytes = max(0, int(subscription.traffic_limit_gb or 0)) * BYTES_PER_GB
        if limit_bytes > 0 and used_bytes > limit_bytes:
            used_bytes = limit_bytes
            baseline = counter - used_bytes

    subscription.metered_traffic_baseline_bytes = baseline
    subscription.metered_traffic_last_counter_bytes = counter
    observed_at = sampled_at or now
    if panel_reset_at is not None and panel_reset_at <= now:
        observed_at = max(observed_at, panel_reset_at)
    subscription.metered_traffic_last_checked_at = observed_at
    subscription.traffic_used_gb = used_bytes / BYTES_PER_GB
    return used_bytes, initialized, renewed


def rebase_metered_counter(
    subscription: Any,
    *,
    panel_counter_bytes: int,
    sampled_at: datetime | None = None,
    panel_reset_at: datetime | None = None,
) -> None:
    """Start counting newly restored access from the accepted panel response."""
    counter = max(0, int(panel_counter_bytes or 0))
    used_bytes = round(max(0.0, float(subscription.traffic_used_gb or 0.0)) * BYTES_PER_GB)
    subscription.metered_traffic_baseline_bytes = counter - used_bytes
    subscription.metered_traffic_last_counter_bytes = counter
    observed_at = sampled_at or datetime.now(UTC)
    if panel_reset_at is not None:
        observed_at = max(observed_at, panel_reset_at)
    subscription.metered_traffic_last_checked_at = observed_at
    subscription.updated_at = datetime.now(UTC)


def cap_metered_usage(subscription: Any) -> bool:
    """Discard overshoot before adding quota or after a temporary quota expires."""
    if not is_metered_traffic_enabled():
        return False
    limit_gb = max(0, int(getattr(subscription, 'traffic_limit_gb', 0) or 0))
    used_gb = max(0.0, float(getattr(subscription, 'traffic_used_gb', 0.0) or 0.0))
    if limit_gb <= 0 or used_gb <= limit_gb:
        return False
    baseline = int(getattr(subscription, 'metered_traffic_baseline_bytes', 0) or 0)
    subscription.metered_traffic_baseline_bytes = baseline + round((used_gb - limit_gb) * BYTES_PER_GB)
    subscription.updated_at = datetime.now(UTC)
    subscription.traffic_used_gb = float(limit_gb)
    return True


def metered_sample_is_stale(subscription: Any, sampled_at: datetime | None) -> bool:
    if sampled_at is None:
        return False
    return any(
        timestamp is not None and timestamp > sampled_at
        for timestamp in (
            getattr(subscription, 'metered_traffic_last_checked_at', None),
            getattr(subscription, 'updated_at', None),
        )
    )


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
    """Remove only technical squads and clear stale metered state."""
    before = extract_squad_uuids(getattr(subscription, 'connected_squads', None))
    for squad_uuid in get_metered_squad_uuids():
        _remove_squad(subscription, squad_uuid)
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

    current_squads = extract_squad_uuids(getattr(subscription, 'connected_squads', None))
    was_blocked = bool(getattr(subscription, 'metered_access_blocked', False))
    metered_squad_uuids = get_metered_squad_uuids()
    was_missing = any(squad_uuid not in current_squads for squad_uuid in metered_squad_uuids)
    for squad_uuid in metered_squad_uuids:
        _add_squad(subscription, squad_uuid)
    subscription.metered_access_blocked = False
    subscription.metered_access_blocked_at = None
    if was_blocked or was_missing:
        subscription.metered_warning_percent = 0
    return was_blocked or was_missing


def block_metered_access(subscription: Any) -> None:
    was_blocked = bool(getattr(subscription, 'metered_access_blocked', False))
    for squad_uuid in get_metered_squad_uuids():
        _remove_squad(subscription, squad_uuid)
    subscription.metered_access_blocked = True
    if not was_blocked or getattr(subscription, 'metered_access_blocked_at', None) is None:
        subscription.metered_access_blocked_at = datetime.now(UTC)
    subscription.metered_warning_percent = 100
