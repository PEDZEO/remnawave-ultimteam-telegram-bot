from app.database.database import AsyncSessionLocal
from app.services.remnawave_service import RemnaWaveService
from app.services.remnawave_sync_service import remnawave_sync_service
from app.utils.startup_timeline import StartupTimeline

from .startup_error_helpers import warn_startup_stage_error
from .types import LoggerLike


async def initialize_remnawave_sync_stage(timeline: StartupTimeline, logger: LoggerLike) -> None:
    async with timeline.stage(
        'Автосинхронизация RemnaWave',
        '🔄',
        success_message='Сервис автосинхронизации готов',
    ) as stage:
        try:
            service = RemnaWaveService()
            if service.is_configured:
                try:
                    async with AsyncSessionLocal() as db:
                        compatibility_stats = await service.reconcile_user_identifiers(db)
                    if compatibility_stats['migrated']:
                        stage.log(
                            'Обновлены идентификаторы Remnawave 3.x: '
                            f"{compatibility_stats['migrated']} из {compatibility_stats['checked']}"
                        )
                except Exception as error:
                    stage.warning(f'Не удалось проверить совместимость Remnawave 3.x: {error}')
                    logger.warning('Remnawave 3.x compatibility reconciliation failed', error=error)

            await remnawave_sync_service.initialize()
            status = remnawave_sync_service.get_status()
            if status.enabled:
                times_text = ', '.join(t.strftime('%H:%M') for t in status.times) or '—'
                if status.next_run:
                    next_run_text = status.next_run.strftime('%d.%m.%Y %H:%M')
                    stage.log(f'Активирована: расписание {times_text}, ближайший запуск {next_run_text}')
                else:
                    stage.log(f'Активирована: расписание {times_text}')
            else:
                stage.log('Автосинхронизация отключена настройками')
        except Exception as error:
            warn_startup_stage_error(
                stage=stage,
                logger=logger,
                stage_error_message='Ошибка запуска автосинхронизации',
                logger_error_message='❌ Ошибка запуска автосинхронизации RemnaWave',
                error=error,
            )
