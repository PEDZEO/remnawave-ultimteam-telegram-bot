from types import SimpleNamespace

from app.cabinet.routes.admin_tariffs import (
    _resolve_tariff_apply_device_limit,
    _resolve_tariff_apply_traffic_limit,
)


def test_apply_tariff_traffic_replaces_unlimited_with_limited_base() -> None:
    tariff = SimpleNamespace(traffic_limit_gb=35)
    subscription = SimpleNamespace(traffic_limit_gb=0, purchased_traffic_gb=0)

    assert _resolve_tariff_apply_traffic_limit(tariff, subscription) == 35


def test_apply_tariff_traffic_preserves_active_topup() -> None:
    tariff = SimpleNamespace(traffic_limit_gb=35)
    subscription = SimpleNamespace(traffic_limit_gb=120, purchased_traffic_gb=20)

    assert _resolve_tariff_apply_traffic_limit(tariff, subscription) == 55


def test_apply_unlimited_tariff_traffic_stays_unlimited_even_with_topup_state() -> None:
    tariff = SimpleNamespace(traffic_limit_gb=0)
    subscription = SimpleNamespace(traffic_limit_gb=120, purchased_traffic_gb=20)

    assert _resolve_tariff_apply_traffic_limit(tariff, subscription) == 0


def test_apply_tariff_device_limit_does_not_drop_existing_extra_slots() -> None:
    tariff = SimpleNamespace(device_limit=2, max_device_limit=None)
    subscription = SimpleNamespace(device_limit=4)

    assert _resolve_tariff_apply_device_limit(tariff, subscription) == 4


def test_apply_tariff_device_limit_respects_tariff_max_limit() -> None:
    tariff = SimpleNamespace(device_limit=2, max_device_limit=3)
    subscription = SimpleNamespace(device_limit=4)

    assert _resolve_tariff_apply_device_limit(tariff, subscription) == 3
