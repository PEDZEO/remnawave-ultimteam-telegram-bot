from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.tap_reward_report_service import (
    TapRewardDailyReportData,
    TapRewardReportService,
    TapRewardUserDailyRow,
)


pytestmark = pytest.mark.asyncio


async def test_tap_reward_daily_report_formats_totals_and_top_rows(monkeypatch):
    service = TapRewardReportService()
    report_date = date(2026, 7, 3)
    data = TapRewardDailyReportData(
        report_date=report_date,
        active_users=2,
        total_taps=150,
        total_rewards=3,
        balance_reward_kopeks=5000,
        subscription_reward_days=2,
        top_rows=[
            TapRewardUserDailyRow(
                user=SimpleNamespace(id=10, telegram_id=123, username='alice', email=None),
                stats=SimpleNamespace(tap_count=120, reward_count=2),
            ),
            TapRewardUserDailyRow(
                user=SimpleNamespace(id=11, telegram_id=None, username=None, email='b@example.test'),
                stats=SimpleNamespace(tap_count=30, reward_count=1),
            ),
        ],
    )
    monkeypatch.setattr(service, '_collect_daily_report_data', AsyncMock(return_value=data))

    text = await service._build_daily_report(report_date)

    assert 'Тапы за 03.07.2026' in text
    assert 'Пользователей тапало: <b>2</b>' in text
    assert 'Всего тапов: <b>150</b>' in text
    assert 'Подарков выдано: <b>3</b>' in text
    assert 'Балансом выдано: <b>50 ₽</b>' in text
    assert 'ID 10 / TG 123 / @alice' in text
    assert 'ID 11 / b@example.test' in text


async def test_tap_reward_daily_report_handles_empty_day(monkeypatch):
    service = TapRewardReportService()
    report_date = date(2026, 7, 3)
    data = TapRewardDailyReportData(
        report_date=report_date,
        active_users=0,
        total_taps=0,
        total_rewards=0,
        balance_reward_kopeks=0,
        subscription_reward_days=0,
        top_rows=[],
    )
    monkeypatch.setattr(service, '_collect_daily_report_data', AsyncMock(return_value=data))

    text = await service._build_daily_report(report_date)

    assert 'Всего тапов: <b>0</b>' in text
    assert 'Тапов за день не было.' in text
