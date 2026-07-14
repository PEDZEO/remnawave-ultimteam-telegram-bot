from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import Subscription, User
from app.services.admin_notification_service import AdminNotificationService
from app.services.trial_parameters_service import resolve_trial_parameters


@pytest.mark.asyncio
async def test_trial_settings_keep_priority_over_selected_tariff(monkeypatch):
    monkeypatch.setattr(settings, 'TRIAL_DURATION_DAYS', 3)
    monkeypatch.setattr(settings, 'TRIAL_TRAFFIC_LIMIT_GB', 2)
    monkeypatch.setattr(settings, 'TRIAL_DEVICE_LIMIT', 1)
    monkeypatch.setattr(settings, 'SALES_MODE', 'tariffs')

    tariff = SimpleNamespace(
        id=17,
        name='Standard + LTE',
        is_active=True,
        traffic_limit_gb=20,
        device_limit=2,
        allowed_squads=['squad-a', 'squad-b'],
    )

    with patch(
        'app.services.trial_parameters_service.get_trial_tariff',
        new=AsyncMock(return_value=tariff),
    ):
        parameters = await resolve_trial_parameters(AsyncMock(spec=AsyncSession))

    assert parameters.duration_days == 3
    assert parameters.traffic_limit_gb == 2
    assert parameters.device_limit == 1
    assert parameters.connected_squads == ['squad-a', 'squad-b']
    assert parameters.tariff_id == 17
    assert parameters.tariff is tariff


@pytest.mark.asyncio
async def test_trial_notification_records_actual_subscription_limits():
    start_date = datetime(2026, 7, 14, 20, 47, tzinfo=UTC)
    subscription = MagicMock(spec=Subscription)
    subscription.start_date = start_date
    subscription.end_date = start_date + timedelta(days=3)
    subscription.traffic_limit_gb = 2
    subscription.device_limit = 1

    service = AdminNotificationService(MagicMock())
    service._record_subscription_event = AsyncMock()
    service._is_enabled = MagicMock(return_value=False)

    sent = await service.send_trial_activation_notification(
        AsyncMock(spec=AsyncSession),
        MagicMock(spec=User),
        subscription,
    )

    assert sent is False
    event = service._record_subscription_event.await_args.kwargs
    assert event['extra']['trial_duration_days'] == 3
    assert event['extra']['traffic_limit_gb'] == 2
    assert event['extra']['device_limit'] == 1
