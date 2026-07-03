import asyncio
from collections.abc import Callable

from app.config import settings
from app.services.payment_verification_service import auto_payment_verification_service
from app.services.reporting_service import reporting_service
from app.services.tap_reward_report_service import tap_reward_report_service
from app.utils.startup_timeline import StartupTimeline


def _format_webhook_url(base_url: str, path: str) -> str:
    return f'{base_url}{path if path.startswith("/") else "/" + path}'


def _collect_webhook_lines(base_url: str, *, telegram_webhook_enabled: bool) -> list[str]:
    webhook_lines: list[str] = []
    telegram_webhook_url = settings.get_telegram_webhook_url()
    if telegram_webhook_enabled and telegram_webhook_url:
        webhook_lines.append(f'Telegram: {telegram_webhook_url}')

    webhook_configs: list[tuple[Callable[[], bool], str, str]] = [
        (lambda: settings.TRIBUTE_ENABLED, 'Tribute', settings.TRIBUTE_WEBHOOK_PATH),
        (settings.is_mulenpay_enabled, settings.get_mulenpay_display_name(), settings.MULENPAY_WEBHOOK_PATH),
        (settings.is_cryptobot_enabled, 'CryptoBot', settings.CRYPTOBOT_WEBHOOK_PATH),
        (settings.is_yookassa_enabled, 'YooKassa', settings.YOOKASSA_WEBHOOK_PATH),
        (settings.is_pal24_enabled, 'PayPalych', settings.PAL24_WEBHOOK_PATH),
        (settings.is_wata_enabled, 'WATA', settings.WATA_WEBHOOK_PATH),
        (settings.is_heleket_enabled, 'Heleket', settings.HELEKET_WEBHOOK_PATH),
        (settings.is_platega_enabled, 'Platega', settings.PLATEGA_WEBHOOK_PATH),
        (settings.is_cloudpayments_enabled, 'CloudPayments', settings.CLOUDPAYMENTS_WEBHOOK_PATH),
        (settings.is_freekassa_enabled, 'Freekassa', settings.FREEKASSA_WEBHOOK_PATH),
        (settings.is_kassa_ai_enabled, 'Kassa.ai', settings.KASSA_AI_WEBHOOK_PATH),
        (settings.is_remnawave_webhook_enabled, 'RemnaWave', settings.REMNAWAVE_WEBHOOK_PATH),
    ]
    for is_enabled, label, path in webhook_configs:
        if is_enabled():
            webhook_lines.append(f'{label}: {_format_webhook_url(base_url, path)}')

    return webhook_lines


def log_startup_summary(
    timeline: StartupTimeline,
    *,
    telegram_webhook_enabled: bool,
    monitoring_task: asyncio.Task | None,
    maintenance_task: asyncio.Task | None,
    traffic_monitoring_task: asyncio.Task | None,
    daily_subscription_task: asyncio.Task | None,
    version_check_task: asyncio.Task | None,
    verification_providers: list[str],
) -> None:
    base_url = settings.WEBHOOK_URL or f'http://{settings.WEB_API_HOST}:{settings.WEB_API_PORT}'
    webhook_lines = _collect_webhook_lines(base_url, telegram_webhook_enabled=telegram_webhook_enabled)

    timeline.log_section(
        'Активные webhook endpoints',
        webhook_lines or ['Нет активных endpoints'],
        icon='🎯',
    )

    services_lines = [
        f'Мониторинг: {"Включен" if monitoring_task else "Отключен"}',
        f'Техработы: {"Включен" if maintenance_task else "Отключен"}',
        f'Мониторинг трафика: {"Включен" if traffic_monitoring_task else "Отключен"}',
        f'Суточные подписки: {"Включен" if daily_subscription_task else "Отключен"}',
        f'Проверка версий: {"Включен" if version_check_task else "Отключен"}',
        f'Отчеты: {"Включен" if reporting_service.is_running() else "Отключен"}',
        f'Отчеты по тапам: {"Включен" if tap_reward_report_service.is_running() else "Отключен"}',
    ]
    services_lines.append('Проверка пополнений: ' + ('Включена' if verification_providers else 'Отключена'))
    services_lines.append(
        'Автопроверка пополнений: ' + ('Включена' if auto_payment_verification_service.is_running() else 'Отключена')
    )
    timeline.log_section('Активные фоновые сервисы', services_lines, icon='📄')

    timeline.log_summary()
