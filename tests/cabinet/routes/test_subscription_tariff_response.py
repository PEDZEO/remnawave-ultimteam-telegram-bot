from types import SimpleNamespace

import pytest

from app.cabinet.routes.subscription import _build_tariff_response


@pytest.mark.asyncio
async def test_tariff_purchase_options_expose_traffic_per_extra_device() -> None:
    tariff = SimpleNamespace(
        id=7,
        name='Standard',
        description=None,
        tier_level=1,
        traffic_limit_gb=35,
        device_limit=2,
        max_device_limit=12,
        device_traffic_gb=35,
        device_price_kopeks=10_000,
        allowed_squads=[],
        period_prices={'30': 30_000},
        is_active=True,
        custom_days_enabled=False,
        price_per_day_kopeks=0,
        min_days=1,
        max_days=365,
        custom_traffic_enabled=False,
        traffic_price_per_gb_kopeks=0,
        min_traffic_gb=1,
        max_traffic_gb=1000,
        traffic_topup_enabled=True,
        max_topup_traffic_gb=1000,
        is_daily=False,
        daily_price_kopeks=0,
        traffic_reset_mode='NO_RESET',
    )

    response = await _build_tariff_response(SimpleNamespace(), tariff)

    assert response['device_traffic_gb'] == 35
    assert response['base_device_limit'] == 2
    assert response['traffic_limit_gb'] == 35
