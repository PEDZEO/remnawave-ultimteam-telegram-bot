from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from sqlalchemy.dialects import postgresql

from app.cabinet.routes.admin_traffic import (
    _current_traffic_expressions,
    _current_traffic_order_by,
    _current_traffic_status_condition,
    _current_traffic_usage_condition,
    _serialize_current_traffic_item,
)


def _subscription(**overrides):
    values = {
        'tariff_id': 3,
        'actual_status': 'active',
        'is_trial': False,
        'traffic_limit_gb': 35,
        'traffic_used_gb': 12.5,
        'metered_access_blocked': False,
        'purchased_traffic_gb': 10,
        'device_bonus_traffic_gb': 35,
        'device_limit': 3,
        'traffic_reset_at': None,
        'metered_traffic_last_checked_at': datetime.now(UTC),
        'end_date': datetime.now(UTC) + timedelta(days=20),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _user():
    return SimpleNamespace(
        id=17,
        telegram_id=123456,
        username='pedzeo',
        email='user@example.com',
        full_name='Test User',
        last_remnawave_sync=None,
    )


def test_current_traffic_item_calculates_remaining_and_percent() -> None:
    item = _serialize_current_traffic_item(
        _user(),
        _subscription(),
        SimpleNamespace(id=3, name='Standard'),
    )

    assert item.traffic_used_gb == 12.5
    assert item.traffic_remaining_gb == 22.5
    assert item.traffic_used_percent == 35.71
    assert item.is_exhausted is False
    assert item.purchased_traffic_gb == 10
    assert item.device_bonus_traffic_gb == 35


def test_current_traffic_item_handles_unlimited_and_blocked_state() -> None:
    unlimited = _serialize_current_traffic_item(
        _user(),
        _subscription(traffic_limit_gb=0, traffic_used_gb=120),
        None,
    )
    blocked = _serialize_current_traffic_item(
        _user(),
        _subscription(traffic_used_gb=30, metered_access_blocked=True),
        None,
    )

    assert unlimited.is_unlimited is True
    assert unlimited.traffic_remaining_gb is None
    assert unlimited.traffic_used_percent is None
    assert blocked.is_exhausted is True


def test_current_traffic_sql_filters_and_sort_are_database_side() -> None:
    now = datetime.now(UTC)
    expressions = _current_traffic_expressions(now)
    condition = _current_traffic_usage_condition('warning', expressions, 80)
    status_condition = _current_traffic_status_condition('current', now)
    order = _current_traffic_order_by('remaining', False, expressions)

    compiled_condition = str(condition.compile(dialect=postgresql.dialect(), compile_kwargs={'literal_binds': True}))
    compiled_status = str(
        status_condition.compile(dialect=postgresql.dialect(), compile_kwargs={'literal_binds': True})
    )
    compiled_order = str(order.compile(dialect=postgresql.dialect(), compile_kwargs={'literal_binds': True}))

    assert 'subscriptions.traffic_limit_gb' in compiled_condition
    assert '>= 80' in compiled_condition
    assert "subscriptions.status IN ('active', 'trial', 'limited')" in compiled_status
    assert 'NULLS LAST' in compiled_order
