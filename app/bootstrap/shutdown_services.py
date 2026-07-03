import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import Dispatcher

from app.bootstrap.types import LoggerLike
from app.config import settings
from app.services.backup_service import backup_service
from app.services.contest_rotation_service import contest_rotation_service
from app.services.daily_subscription_service import daily_subscription_service
from app.services.log_rotation_service import log_rotation_service
from app.services.maintenance_service import maintenance_service
from app.services.monitoring_service import monitoring_service
from app.services.nalogo_queue_service import nalogo_queue_service
from app.services.payment_verification_service import auto_payment_verification_service
from app.services.referral_contest_service import referral_contest_service
from app.services.remnawave_sync_service import remnawave_sync_service
from app.services.reporting_service import reporting_service
from app.services.tap_reward_report_service import tap_reward_report_service
from app.services.traffic_monitoring_service import traffic_monitoring_scheduler


async def _cancel_task_if_running(task: asyncio.Task | None) -> None:
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def _safe_shutdown_call(
    logger: LoggerLike,
    *,
    info_message: str,
    error_message: str,
    shutdown_call: Callable[[], Awaitable[Any] | Any],
) -> None:
    logger.info(info_message)
    try:
        result = shutdown_call()
        if inspect.isawaitable(result):
            await result
    except Exception as error:
        logger.error(error_message, error=error)


async def _shutdown_runtime_task(
    logger: LoggerLike,
    *,
    task: asyncio.Task | None,
    info_message: str,
    shutdown_call: Callable[[], Awaitable[Any] | Any] | None = None,
    error_message: str | None = None,
) -> None:
    if task and not task.done():
        logger.info(info_message)
        if shutdown_call is not None and error_message is not None:
            try:
                result = shutdown_call()
                if inspect.isawaitable(result):
                    await result
            except Exception as error:
                logger.error(error_message, error=error)
    await _cancel_task_if_running(task)


async def _run_safe_shutdown_calls(
    logger: LoggerLike,
    *,
    shutdown_calls: tuple[tuple[str, str, Callable[[], Awaitable[Any] | Any]], ...],
) -> None:
    for info_message, error_message, shutdown_call in shutdown_calls:
        await _safe_shutdown_call(
            logger,
            info_message=info_message,
            error_message=error_message,
            shutdown_call=shutdown_call,
        )


async def shutdown_runtime_services(
    logger: LoggerLike,
    *,
    monitoring_task: asyncio.Task | None,
    maintenance_task: asyncio.Task | None,
    version_check_task: asyncio.Task | None,
    traffic_monitoring_task: asyncio.Task | None,
    daily_subscription_task: asyncio.Task | None,
    polling_task: asyncio.Task | None,
    dp: Dispatcher | None,
) -> None:
    await _safe_shutdown_call(
        logger,
        info_message='ℹ️ Остановка сервиса автопроверки пополнений...',
        error_message='Ошибка остановки сервиса автопроверки пополнений',
        shutdown_call=auto_payment_verification_service.stop,
    )

    await _shutdown_runtime_task(
        logger,
        task=monitoring_task,
        info_message='ℹ️ Остановка службы мониторинга...',
        shutdown_call=monitoring_service.stop_monitoring,
        error_message='Ошибка остановки службы мониторинга',
    )
    await _shutdown_runtime_task(
        logger,
        task=maintenance_task,
        info_message='ℹ️ Остановка службы техработ...',
        shutdown_call=maintenance_service.stop_monitoring,
        error_message='Ошибка остановки службы техработ',
    )
    await _shutdown_runtime_task(
        logger,
        task=version_check_task,
        info_message='ℹ️ Остановка сервиса проверки версий...',
    )
    await _shutdown_runtime_task(
        logger,
        task=traffic_monitoring_task,
        info_message='ℹ️ Остановка мониторинга трафика...',
        shutdown_call=traffic_monitoring_scheduler.stop_monitoring,
        error_message='Ошибка остановки мониторинга трафика',
    )
    await _shutdown_runtime_task(
        logger,
        task=daily_subscription_task,
        info_message='ℹ️ Остановка сервиса суточных подписок...',
        shutdown_call=daily_subscription_service.stop_monitoring,
        error_message='Ошибка остановки сервиса суточных подписок',
    )

    await _run_safe_shutdown_calls(
        logger,
        shutdown_calls=(
            (
                'ℹ️ Остановка сервиса отчетов...',
                'Ошибка остановки сервиса отчетов',
                reporting_service.stop,
            ),
            (
                'Остановка отчетов по тапам...',
                'Ошибка остановки отчетов по тапам',
                tap_reward_report_service.stop,
            ),
            (
                'ℹ️ Остановка сервиса конкурсов...',
                'Ошибка остановки сервиса конкурсов',
                referral_contest_service.stop,
            ),
            (
                'ℹ️ Остановка сервиса автосинхронизации RemnaWave...',
                'Ошибка остановки автосинхронизации RemnaWave',
                remnawave_sync_service.stop,
            ),
            (
                'ℹ️ Остановка ротации игр...',
                'Ошибка остановки ротации игр',
                contest_rotation_service.stop,
            ),
        ),
    )

    if settings.is_log_rotation_enabled():
        await _safe_shutdown_call(
            logger,
            info_message='ℹ️ Остановка сервиса ротации логов...',
            error_message='Ошибка остановки сервиса ротации логов',
            shutdown_call=log_rotation_service.stop,
        )

    await _run_safe_shutdown_calls(
        logger,
        shutdown_calls=(
            (
                'ℹ️ Остановка очереди чеков NaloGO...',
                'Ошибка остановки очереди чеков NaloGO',
                nalogo_queue_service.stop,
            ),
            (
                'ℹ️ Остановка сервиса бекапов...',
                'Ошибка остановки сервиса бекапов',
                backup_service.stop_auto_backup,
            ),
        ),
    )

    if polling_task and not polling_task.done():
        logger.info('ℹ️ Остановка polling...')
        if dp is not None:
            try:
                await dp.stop_polling()
            except Exception as error:
                logger.error('Ошибка корректной остановки polling', error=error)
    await _cancel_task_if_running(polling_task)
