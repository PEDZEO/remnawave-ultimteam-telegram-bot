from types import SimpleNamespace

from app.cabinet.routes.admin_tariffs import (
    _apply_tariff_limits_to_subscription,
    _resolve_tariff_apply_device_limit,
    _resolve_tariff_apply_traffic_limit,
)
from app.cabinet.schemas.tariffs import TariffApplyLimitsRequest


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


def test_apply_limits_request_keeps_devices_by_default() -> None:
    request = TariffApplyLimitsRequest()

    assert request.update_device_limit is False
    assert request.reset_traffic_usage is False


def test_apply_limits_persistence_keeps_device_limit_without_flag() -> None:
    subscription = SimpleNamespace(
        traffic_limit_gb=10,
        traffic_used_gb=7.5,
        device_limit=4,
        subscription_url='old-url',
        subscription_crypto_link='old-crypto',
    )

    _apply_tariff_limits_to_subscription(
        subscription,
        target_traffic_limit=35,
        target_device_limit=2,
        subscription_url='new-url',
        crypto_link='new-crypto',
        update_device_limit=False,
        reset_traffic_usage=False,
    )

    assert subscription.traffic_limit_gb == 35
    assert subscription.traffic_used_gb == 7.5
    assert subscription.device_limit == 4
    assert subscription.subscription_url == 'new-url'
    assert subscription.subscription_crypto_link == 'new-crypto'


def test_apply_limits_persistence_updates_device_limit_with_flag() -> None:
    subscription = SimpleNamespace(
        traffic_limit_gb=10,
        traffic_used_gb=7.5,
        device_limit=4,
        subscription_url='old-url',
        subscription_crypto_link='old-crypto',
    )

    _apply_tariff_limits_to_subscription(
        subscription,
        target_traffic_limit=35,
        target_device_limit=2,
        subscription_url='new-url',
        crypto_link='new-crypto',
        update_device_limit=True,
        reset_traffic_usage=False,
    )

    assert subscription.traffic_limit_gb == 35
    assert subscription.traffic_used_gb == 7.5
    assert subscription.device_limit == 2
    assert subscription.subscription_url == 'new-url'
    assert subscription.subscription_crypto_link == 'new-crypto'


def test_apply_limits_persistence_resets_used_traffic_with_flag() -> None:
    subscription = SimpleNamespace(
        traffic_limit_gb=10,
        traffic_used_gb=7.5,
        device_limit=4,
        subscription_url='old-url',
        subscription_crypto_link='old-crypto',
    )

    _apply_tariff_limits_to_subscription(
        subscription,
        target_traffic_limit=35,
        target_device_limit=None,
        subscription_url='new-url',
        crypto_link='new-crypto',
        update_device_limit=False,
        reset_traffic_usage=True,
    )

    assert subscription.traffic_limit_gb == 35
    assert subscription.traffic_used_gb == 0.0
    assert subscription.device_limit == 4
    assert subscription.subscription_url == 'new-url'
    assert subscription.subscription_crypto_link == 'new-crypto'
