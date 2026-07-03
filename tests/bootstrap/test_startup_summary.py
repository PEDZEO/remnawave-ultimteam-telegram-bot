from __future__ import annotations

from types import SimpleNamespace

from app.bootstrap import startup_summary


class _TimelineRecorder:
    def __init__(self) -> None:
        self.sections: list[tuple[str, list[str], str]] = []
        self.summary_called = False

    def log_section(self, title: str, lines: list[str], icon: str) -> None:
        self.sections.append((title, list(lines), icon))

    def log_summary(self) -> None:
        self.summary_called = True


def _build_fake_settings(**overrides):
    defaults = {
        'WEBHOOK_URL': '',
        'WEB_API_HOST': '127.0.0.1',
        'WEB_API_PORT': 8080,
        'TRIBUTE_ENABLED': False,
        'TRIBUTE_WEBHOOK_PATH': '/tribute',
        'MULENPAY_WEBHOOK_PATH': '/mulenpay',
        'CRYPTOBOT_WEBHOOK_PATH': '/cryptobot',
        'YOOKASSA_WEBHOOK_PATH': '/yookassa',
        'PAL24_WEBHOOK_PATH': '/pal24',
        'WATA_WEBHOOK_PATH': '/wata',
        'HELEKET_WEBHOOK_PATH': '/heleket',
        'PLATEGA_WEBHOOK_PATH': '/platega',
        'CLOUDPAYMENTS_WEBHOOK_PATH': '/cloudpayments',
        'FREEKASSA_WEBHOOK_PATH': '/freekassa',
        'KASSA_AI_WEBHOOK_PATH': '/kassa-ai',
        'REMNAWAVE_WEBHOOK_PATH': '/remnawave',
        'get_telegram_webhook_url': lambda: None,
        'get_mulenpay_display_name': lambda: 'MulenPay',
        'is_mulenpay_enabled': lambda: False,
        'is_cryptobot_enabled': lambda: False,
        'is_yookassa_enabled': lambda: False,
        'is_pal24_enabled': lambda: False,
        'is_wata_enabled': lambda: False,
        'is_heleket_enabled': lambda: False,
        'is_platega_enabled': lambda: False,
        'is_cloudpayments_enabled': lambda: False,
        'is_freekassa_enabled': lambda: False,
        'is_kassa_ai_enabled': lambda: False,
        'is_remnawave_webhook_enabled': lambda: False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_log_startup_summary_uses_fallback_when_no_webhooks(monkeypatch) -> None:
    timeline = _TimelineRecorder()
    monkeypatch.setattr(startup_summary, 'settings', _build_fake_settings())
    monkeypatch.setattr(startup_summary, 'reporting_service', SimpleNamespace(is_running=lambda: False))
    monkeypatch.setattr(startup_summary, 'tap_reward_report_service', SimpleNamespace(is_running=lambda: False))
    monkeypatch.setattr(
        startup_summary,
        'auto_payment_verification_service',
        SimpleNamespace(is_running=lambda: False),
    )

    startup_summary.log_startup_summary(
        timeline,
        telegram_webhook_enabled=False,
        monitoring_task=None,
        maintenance_task=None,
        traffic_monitoring_task=None,
        daily_subscription_task=None,
        version_check_task=None,
        verification_providers=[],
    )

    webhook_section = timeline.sections[0]
    assert webhook_section[0] == 'Активные webhook endpoints'
    assert webhook_section[1] == ['Нет активных endpoints']
    assert timeline.summary_called is True


def test_log_startup_summary_collects_enabled_webhooks_in_order(monkeypatch) -> None:
    timeline = _TimelineRecorder()
    monkeypatch.setattr(
        startup_summary,
        'settings',
        _build_fake_settings(
            WEBHOOK_URL='https://example.test',
            TRIBUTE_ENABLED=True,
            get_telegram_webhook_url=lambda: 'https://t.me/webhook',
            is_mulenpay_enabled=lambda: True,
            is_cryptobot_enabled=lambda: True,
            CRYPTOBOT_WEBHOOK_PATH='cryptobot',
        ),
    )
    monkeypatch.setattr(startup_summary, 'reporting_service', SimpleNamespace(is_running=lambda: True))
    monkeypatch.setattr(startup_summary, 'tap_reward_report_service', SimpleNamespace(is_running=lambda: True))
    monkeypatch.setattr(
        startup_summary,
        'auto_payment_verification_service',
        SimpleNamespace(is_running=lambda: True),
    )

    startup_summary.log_startup_summary(
        timeline,
        telegram_webhook_enabled=True,
        monitoring_task=SimpleNamespace(),
        maintenance_task=None,
        traffic_monitoring_task=None,
        daily_subscription_task=None,
        version_check_task=None,
        verification_providers=['m'],
    )

    webhook_section = timeline.sections[0]
    assert webhook_section[1][:4] == [
        'Telegram: https://t.me/webhook',
        'Tribute: https://example.test/tribute',
        'MulenPay: https://example.test/mulenpay',
        'CryptoBot: https://example.test/cryptobot',
    ]
