from dataclasses import dataclass

from aiogram import Bot, Dispatcher

from app.bootstrap.backup_startup import initialize_backup_stage
from app.bootstrap.bot_startup import setup_bot_stage
from app.bootstrap.configuration_startup import load_bot_configuration_stage
from app.bootstrap.contest_rotation_startup import initialize_contest_rotation_stage
from app.bootstrap.database_initialization import initialize_database_stage
from app.bootstrap.database_startup import run_database_migration_stage
from app.bootstrap.external_admin_startup import initialize_external_admin_stage
from app.bootstrap.log_rotation_startup import initialize_log_rotation_stage
from app.bootstrap.nalogo_queue_startup import start_nalogo_queue_stage
from app.bootstrap.payment_methods_startup import initialize_payment_methods_stage
from app.bootstrap.payment_runtime import setup_payment_runtime
from app.bootstrap.payment_verification_startup import initialize_payment_verification_stage
from app.bootstrap.referral_contests_startup import initialize_referral_contests_stage
from app.bootstrap.remnawave_sync_startup import initialize_remnawave_sync_stage
from app.bootstrap.reporting_startup import initialize_reporting_stage
from app.bootstrap.runtime_mode import resolve_runtime_mode
from app.bootstrap.servers_startup import sync_servers_stage
from app.bootstrap.services_startup import connect_integration_services_stage, wire_core_services
from app.bootstrap.tap_reward_reports_startup import initialize_tap_reward_reports_stage
from app.bootstrap.tariffs_startup import sync_tariffs_stage
from app.bootstrap.telegram_webhook_startup import configure_telegram_webhook_stage
from app.bootstrap.types import LoggerLike, TelegramNotifierLike
from app.bootstrap.web_server_startup import start_web_server_stage
from app.config import settings
from app.services.payment_service import PaymentService
from app.utils.startup_timeline import StartupTimeline
from app.webapi.server import WebAPIServer


@dataclass
class CoreRuntimeStartupContext:
    bot: Bot
    dp: Dispatcher
    payment_service: PaymentService
    verification_providers: list[str]
    auto_verification_active: bool
    polling_enabled: bool
    telegram_webhook_enabled: bool
    web_api_server: WebAPIServer | None


@dataclass(frozen=True)
class RuntimeModeFlags:
    polling_enabled: bool
    telegram_webhook_enabled: bool
    payment_webhooks_enabled: bool


@dataclass(frozen=True)
class PreRuntimeBootstrapResult:
    bot: Bot
    dp: Dispatcher


@dataclass(frozen=True)
class PostPaymentBootstrapResult:
    verification_providers: list[str]
    auto_verification_active: bool


@dataclass(frozen=True)
class WebStartupResult:
    web_api_server: WebAPIServer | None


def _resolve_runtime_flags() -> RuntimeModeFlags:
    polling_enabled, telegram_webhook_enabled, payment_webhooks_enabled = resolve_runtime_mode()
    return RuntimeModeFlags(
        polling_enabled=polling_enabled,
        telegram_webhook_enabled=telegram_webhook_enabled,
        payment_webhooks_enabled=payment_webhooks_enabled,
    )


async def _run_pre_runtime_bootstrap(
    timeline: StartupTimeline,
    logger: LoggerLike,
    telegram_notifier: TelegramNotifierLike,
) -> PreRuntimeBootstrapResult:
    await run_database_migration_stage(timeline, logger)
    await initialize_database_stage(timeline)
    await sync_tariffs_stage(timeline, logger)
    await sync_servers_stage(timeline, logger)
    await initialize_payment_methods_stage(timeline, logger)
    await load_bot_configuration_stage(timeline, logger)

    bot, dp = await setup_bot_stage(timeline)
    wire_core_services(bot, telegram_notifier)
    await connect_integration_services_stage(timeline, bot)

    await initialize_backup_stage(timeline, logger, bot)
    await initialize_reporting_stage(timeline, logger, bot)
    await initialize_tap_reward_reports_stage(timeline, logger, bot)
    await initialize_referral_contests_stage(timeline, logger)
    await initialize_contest_rotation_stage(timeline, logger, bot)
    if settings.is_log_rotation_enabled():
        await initialize_log_rotation_stage(timeline, logger, bot)

    await initialize_remnawave_sync_stage(timeline, logger)
    return PreRuntimeBootstrapResult(bot=bot, dp=dp)


async def _run_post_payment_bootstrap(
    timeline: StartupTimeline,
    logger: LoggerLike,
    *,
    bot: Bot,
    payment_service: PaymentService,
) -> PostPaymentBootstrapResult:
    verification_providers, auto_verification_active = await initialize_payment_verification_stage(timeline)
    await start_nalogo_queue_stage(timeline, logger, payment_service)
    await initialize_external_admin_stage(timeline, logger, bot)
    return PostPaymentBootstrapResult(
        verification_providers=verification_providers,
        auto_verification_active=auto_verification_active,
    )


async def _run_web_startup_bootstrap(
    timeline: StartupTimeline,
    *,
    bot: Bot,
    dp: Dispatcher,
    payment_service: PaymentService,
    runtime_flags: RuntimeModeFlags,
) -> WebStartupResult:
    _web_app, web_api_server = await start_web_server_stage(
        timeline,
        bot,
        dp,
        payment_service,
        telegram_webhook_enabled=runtime_flags.telegram_webhook_enabled,
        payment_webhooks_enabled=runtime_flags.payment_webhooks_enabled,
    )
    await configure_telegram_webhook_stage(
        timeline,
        bot,
        dp,
        telegram_webhook_enabled=runtime_flags.telegram_webhook_enabled,
    )
    return WebStartupResult(web_api_server=web_api_server)


def _build_core_runtime_startup_context(
    *,
    bot: Bot,
    dp: Dispatcher,
    payment_service: PaymentService,
    post_payment_bootstrap_result: PostPaymentBootstrapResult,
    runtime_flags: RuntimeModeFlags,
    web_startup_result: WebStartupResult,
) -> CoreRuntimeStartupContext:
    return CoreRuntimeStartupContext(
        bot=bot,
        dp=dp,
        payment_service=payment_service,
        verification_providers=post_payment_bootstrap_result.verification_providers,
        auto_verification_active=post_payment_bootstrap_result.auto_verification_active,
        polling_enabled=runtime_flags.polling_enabled,
        telegram_webhook_enabled=runtime_flags.telegram_webhook_enabled,
        web_api_server=web_startup_result.web_api_server,
    )


async def start_core_runtime_stage(
    timeline: StartupTimeline,
    logger: LoggerLike,
    telegram_notifier: TelegramNotifierLike,
) -> CoreRuntimeStartupContext:
    pre_runtime_bootstrap_result = await _run_pre_runtime_bootstrap(timeline, logger, telegram_notifier)
    bot = pre_runtime_bootstrap_result.bot
    dp = pre_runtime_bootstrap_result.dp

    payment_service = setup_payment_runtime(bot)
    post_payment_bootstrap_result = await _run_post_payment_bootstrap(
        timeline,
        logger,
        bot=bot,
        payment_service=payment_service,
    )

    runtime_flags = _resolve_runtime_flags()
    web_startup_result = await _run_web_startup_bootstrap(
        timeline,
        bot=bot,
        dp=dp,
        payment_service=payment_service,
        runtime_flags=runtime_flags,
    )

    return _build_core_runtime_startup_context(
        bot=bot,
        dp=dp,
        payment_service=payment_service,
        post_payment_bootstrap_result=post_payment_bootstrap_result,
        runtime_flags=runtime_flags,
        web_startup_result=web_startup_result,
    )
