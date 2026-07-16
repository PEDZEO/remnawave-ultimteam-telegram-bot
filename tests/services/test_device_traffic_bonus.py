from types import SimpleNamespace

from app.services.device_traffic_bonus import (
    apply_device_traffic_bonus,
    calculate_device_traffic_bonus,
    rebuild_traffic_with_device_bonus,
)


def _tariff(*, base_devices: int = 2, traffic_per_device: int = 35):
    return SimpleNamespace(device_limit=base_devices, device_traffic_gb=traffic_per_device)


def _subscription(
    *,
    devices: int,
    total_traffic: int,
    purchased_traffic: int = 0,
    device_bonus: int = 0,
):
    return SimpleNamespace(
        device_limit=devices,
        traffic_limit_gb=total_traffic,
        purchased_traffic_gb=purchased_traffic,
        device_bonus_traffic_gb=device_bonus,
    )


def test_calculates_bonus_only_for_devices_above_tariff_base() -> None:
    assert calculate_device_traffic_bonus(_tariff(), 2) == 0
    assert calculate_device_traffic_bonus(_tariff(), 12) == 350


def test_apply_is_idempotent_and_preserves_temporary_traffic() -> None:
    subscription = _subscription(devices=12, total_traffic=55, purchased_traffic=20)

    assert apply_device_traffic_bonus(subscription, _tariff()) == 350
    assert subscription.traffic_limit_gb == 405
    assert subscription.device_bonus_traffic_gb == 350

    assert apply_device_traffic_bonus(subscription, _tariff()) == 0
    assert subscription.traffic_limit_gb == 405


def test_reducing_devices_removes_only_device_bonus() -> None:
    subscription = _subscription(devices=2, total_traffic=405, purchased_traffic=20, device_bonus=350)

    assert apply_device_traffic_bonus(subscription, _tariff()) == -350
    assert subscription.traffic_limit_gb == 55
    assert subscription.purchased_traffic_gb == 20


def test_unlimited_subscription_never_gets_finite_device_bonus() -> None:
    subscription = _subscription(devices=12, total_traffic=0)

    assert apply_device_traffic_bonus(subscription, _tariff()) == 0
    assert subscription.traffic_limit_gb == 0
    assert subscription.device_bonus_traffic_gb == 0


def test_rebuild_combines_base_purchases_and_device_bonus() -> None:
    subscription = _subscription(devices=12, total_traffic=0, purchased_traffic=20)

    total = rebuild_traffic_with_device_bonus(subscription, _tariff(), 35)

    assert total == 405
    assert subscription.device_bonus_traffic_gb == 350
