from __future__ import annotations

import importlib
import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest


# Prevent heavy aiogram/redis import chain from app.bootstrap.bot_startup during module import.
if 'app.bootstrap.bot_startup' not in sys.modules:
    bot_startup_stub = types.ModuleType('app.bootstrap.bot_startup')

    async def _setup_bot_stage(*_args, **_kwargs):
        return MagicMock(), MagicMock()

    bot_startup_stub.setup_bot_stage = _setup_bot_stage
    sys.modules['app.bootstrap.bot_startup'] = bot_startup_stub


@pytest.mark.asyncio
async def test_start_core_runtime_stage_propagates_runtime_mode_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    startup = importlib.import_module('app.bootstrap.core_runtime_startup')
    if not hasattr(startup, 'run_database_migration_stage'):
        sys.modules.pop('app.bootstrap.core_runtime_startup', None)
        startup = importlib.import_module('app.bootstrap.core_runtime_startup')

    timeline = MagicMock()
    logger = MagicMock()
    telegram_notifier = MagicMock()
    bot = MagicMock()
    dp = MagicMock()
    payment_service = MagicMock()
    web_api_server = MagicMock()
    call_order: list[str] = []

    monkeypatch.setattr(startup, 'run_database_migration_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_database_stage', AsyncMock())
    monkeypatch.setattr(startup, 'sync_tariffs_stage', AsyncMock())
    monkeypatch.setattr(startup, 'sync_servers_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_payment_methods_stage', AsyncMock())
    monkeypatch.setattr(startup, 'load_bot_configuration_stage', AsyncMock())
    monkeypatch.setattr(startup, 'setup_bot_stage', AsyncMock(return_value=(bot, dp)))
    monkeypatch.setattr(startup, 'wire_core_services', MagicMock())
    monkeypatch.setattr(startup, 'connect_integration_services_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_backup_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_reporting_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_tap_reward_reports_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_referral_contests_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_contest_rotation_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_log_rotation_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_remnawave_sync_stage', AsyncMock())
    monkeypatch.setattr(startup, 'setup_payment_runtime', lambda _bot: payment_service)

    async def _initialize_payment_verification_stage(*_args, **_kwargs):
        call_order.append('payment_verification')
        return ['provider-1'], True

    async def _start_nalogo_queue_stage(*_args, **_kwargs):
        call_order.append('nalogo_queue')

    async def _initialize_external_admin_stage(*_args, **_kwargs):
        call_order.append('external_admin')

    monkeypatch.setattr(
        startup,
        'initialize_payment_verification_stage',
        AsyncMock(side_effect=_initialize_payment_verification_stage),
    )
    monkeypatch.setattr(startup, 'start_nalogo_queue_stage', AsyncMock(side_effect=_start_nalogo_queue_stage))
    monkeypatch.setattr(
        startup,
        'initialize_external_admin_stage',
        AsyncMock(side_effect=_initialize_external_admin_stage),
    )
    monkeypatch.setattr(
        startup,
        'resolve_runtime_mode',
        lambda: (False, True, False),
    )
    start_web_server_stage = AsyncMock(return_value=(None, web_api_server))
    monkeypatch.setattr(startup, 'start_web_server_stage', start_web_server_stage)
    configure_telegram_webhook_stage = AsyncMock()
    monkeypatch.setattr(startup, 'configure_telegram_webhook_stage', configure_telegram_webhook_stage)
    monkeypatch.setattr(startup, 'settings', types.SimpleNamespace(is_log_rotation_enabled=lambda: True))

    result = await startup.start_core_runtime_stage(timeline, logger, telegram_notifier)

    assert result.bot is bot
    assert result.dp is dp
    assert result.payment_service is payment_service
    assert result.verification_providers == ['provider-1']
    assert result.auto_verification_active is True
    assert result.polling_enabled is False
    assert result.telegram_webhook_enabled is True
    assert result.web_api_server is web_api_server

    start_web_server_stage.assert_awaited_once_with(
        timeline,
        bot,
        dp,
        payment_service,
        telegram_webhook_enabled=True,
        payment_webhooks_enabled=False,
    )
    configure_telegram_webhook_stage.assert_awaited_once_with(
        timeline,
        bot,
        dp,
        telegram_webhook_enabled=True,
    )
    assert call_order == ['payment_verification', 'nalogo_queue', 'external_admin']


@pytest.mark.asyncio
async def test_run_pre_runtime_bootstrap_preserves_sequence_and_bot_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    startup = importlib.import_module('app.bootstrap.core_runtime_startup')
    if not hasattr(startup, 'run_database_migration_stage'):
        sys.modules.pop('app.bootstrap.core_runtime_startup', None)
        startup = importlib.import_module('app.bootstrap.core_runtime_startup')

    timeline = MagicMock()
    logger = MagicMock()
    telegram_notifier = MagicMock()
    bot = MagicMock()
    dp = MagicMock()
    call_order: list[str] = []

    async def _run_database_migration_stage(*_args, **_kwargs):
        call_order.append('db_migration')

    async def _initialize_database_stage(*_args, **_kwargs):
        call_order.append('db_init')

    async def _sync_tariffs_stage(*_args, **_kwargs):
        call_order.append('sync_tariffs')

    async def _sync_servers_stage(*_args, **_kwargs):
        call_order.append('sync_servers')

    async def _initialize_payment_methods_stage(*_args, **_kwargs):
        call_order.append('payment_methods')

    async def _load_bot_configuration_stage(*_args, **_kwargs):
        call_order.append('load_bot_config')

    async def _setup_bot_stage(*_args, **_kwargs):
        call_order.append('setup_bot')
        return bot, dp

    def _wire_core_services(*_args, **_kwargs):
        call_order.append('wire_core_services')

    async def _connect_integration_services_stage(*_args, **_kwargs):
        call_order.append('connect_integrations')

    async def _initialize_backup_stage(*_args, **_kwargs):
        call_order.append('backup')

    async def _initialize_reporting_stage(*_args, **_kwargs):
        call_order.append('reporting')

    async def _initialize_tap_reward_reports_stage(*_args, **_kwargs):
        call_order.append('tap_reward_reports')

    async def _initialize_referral_contests_stage(*_args, **_kwargs):
        call_order.append('referral_contests')

    async def _initialize_contest_rotation_stage(*_args, **_kwargs):
        call_order.append('contest_rotation')

    async def _initialize_log_rotation_stage(*_args, **_kwargs):
        call_order.append('log_rotation')

    async def _initialize_remnawave_sync_stage(*_args, **_kwargs):
        call_order.append('remnawave_sync')

    monkeypatch.setattr(startup, 'run_database_migration_stage', AsyncMock(side_effect=_run_database_migration_stage))
    monkeypatch.setattr(startup, 'initialize_database_stage', AsyncMock(side_effect=_initialize_database_stage))
    monkeypatch.setattr(startup, 'sync_tariffs_stage', AsyncMock(side_effect=_sync_tariffs_stage))
    monkeypatch.setattr(startup, 'sync_servers_stage', AsyncMock(side_effect=_sync_servers_stage))
    monkeypatch.setattr(
        startup,
        'initialize_payment_methods_stage',
        AsyncMock(side_effect=_initialize_payment_methods_stage),
    )
    monkeypatch.setattr(startup, 'load_bot_configuration_stage', AsyncMock(side_effect=_load_bot_configuration_stage))
    monkeypatch.setattr(startup, 'setup_bot_stage', AsyncMock(side_effect=_setup_bot_stage))
    monkeypatch.setattr(startup, 'wire_core_services', MagicMock(side_effect=_wire_core_services))
    monkeypatch.setattr(
        startup,
        'connect_integration_services_stage',
        AsyncMock(side_effect=_connect_integration_services_stage),
    )
    monkeypatch.setattr(startup, 'initialize_backup_stage', AsyncMock(side_effect=_initialize_backup_stage))
    monkeypatch.setattr(startup, 'initialize_reporting_stage', AsyncMock(side_effect=_initialize_reporting_stage))
    monkeypatch.setattr(
        startup,
        'initialize_tap_reward_reports_stage',
        AsyncMock(side_effect=_initialize_tap_reward_reports_stage),
    )
    monkeypatch.setattr(
        startup,
        'initialize_referral_contests_stage',
        AsyncMock(side_effect=_initialize_referral_contests_stage),
    )
    monkeypatch.setattr(
        startup,
        'initialize_contest_rotation_stage',
        AsyncMock(side_effect=_initialize_contest_rotation_stage),
    )
    monkeypatch.setattr(startup, 'initialize_log_rotation_stage', AsyncMock(side_effect=_initialize_log_rotation_stage))
    monkeypatch.setattr(
        startup,
        'initialize_remnawave_sync_stage',
        AsyncMock(side_effect=_initialize_remnawave_sync_stage),
    )
    monkeypatch.setattr(startup, 'settings', types.SimpleNamespace(is_log_rotation_enabled=lambda: True))

    result = await startup._run_pre_runtime_bootstrap(timeline, logger, telegram_notifier)

    assert result.bot is bot
    assert result.dp is dp
    assert call_order == [
        'db_migration',
        'db_init',
        'sync_tariffs',
        'sync_servers',
        'payment_methods',
        'load_bot_config',
        'setup_bot',
        'wire_core_services',
        'connect_integrations',
        'backup',
        'reporting',
        'tap_reward_reports',
        'referral_contests',
        'contest_rotation',
        'log_rotation',
        'remnawave_sync',
    ]


@pytest.mark.asyncio
async def test_run_web_startup_bootstrap_propagates_runtime_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    startup = importlib.import_module('app.bootstrap.core_runtime_startup')
    if not hasattr(startup, '_run_web_startup_bootstrap'):
        sys.modules.pop('app.bootstrap.core_runtime_startup', None)
        startup = importlib.import_module('app.bootstrap.core_runtime_startup')

    timeline = MagicMock()
    bot = MagicMock()
    dp = MagicMock()
    payment_service = MagicMock()
    runtime_flags = startup.RuntimeModeFlags(
        polling_enabled=False,
        telegram_webhook_enabled=True,
        payment_webhooks_enabled=False,
    )
    web_api_server = MagicMock()
    start_web_server_stage = AsyncMock(return_value=(None, web_api_server))
    configure_telegram_webhook_stage = AsyncMock()
    monkeypatch.setattr(startup, 'start_web_server_stage', start_web_server_stage)
    monkeypatch.setattr(startup, 'configure_telegram_webhook_stage', configure_telegram_webhook_stage)

    result = await startup._run_web_startup_bootstrap(
        timeline,
        bot=bot,
        dp=dp,
        payment_service=payment_service,
        runtime_flags=runtime_flags,
    )

    assert result.web_api_server is web_api_server
    start_web_server_stage.assert_awaited_once_with(
        timeline,
        bot,
        dp,
        payment_service,
        telegram_webhook_enabled=True,
        payment_webhooks_enabled=False,
    )
    configure_telegram_webhook_stage.assert_awaited_once_with(
        timeline,
        bot,
        dp,
        telegram_webhook_enabled=True,
    )


def test_build_core_runtime_startup_context_maps_all_fields() -> None:
    startup = importlib.import_module('app.bootstrap.core_runtime_startup')
    if not hasattr(startup, '_build_core_runtime_startup_context'):
        sys.modules.pop('app.bootstrap.core_runtime_startup', None)
        startup = importlib.import_module('app.bootstrap.core_runtime_startup')

    bot = MagicMock()
    dp = MagicMock()
    payment_service = MagicMock()
    post_payment_bootstrap_result = startup.PostPaymentBootstrapResult(
        verification_providers=['provider-a', 'provider-b'],
        auto_verification_active=True,
    )
    runtime_flags = startup.RuntimeModeFlags(
        polling_enabled=False,
        telegram_webhook_enabled=True,
        payment_webhooks_enabled=False,
    )
    web_startup_result = startup.WebStartupResult(web_api_server=MagicMock())

    context = startup._build_core_runtime_startup_context(
        bot=bot,
        dp=dp,
        payment_service=payment_service,
        post_payment_bootstrap_result=post_payment_bootstrap_result,
        runtime_flags=runtime_flags,
        web_startup_result=web_startup_result,
    )

    assert context.bot is bot
    assert context.dp is dp
    assert context.payment_service is payment_service
    assert context.verification_providers == ['provider-a', 'provider-b']
    assert context.auto_verification_active is True
    assert context.polling_enabled is False
    assert context.telegram_webhook_enabled is True
    assert context.web_api_server is web_startup_result.web_api_server
