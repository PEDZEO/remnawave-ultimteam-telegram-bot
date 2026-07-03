from aiogram import Bot

from app.services.tap_reward_report_service import tap_reward_report_service
from app.utils.startup_timeline import StartupTimeline

from .startup_error_helpers import warn_startup_stage_error
from .types import LoggerLike


async def initialize_tap_reward_reports_stage(
    timeline: StartupTimeline,
    logger: LoggerLike,
    bot: Bot,
) -> None:
    async with timeline.stage(
        'Отчеты по тапам',
        '🎁',
        success_message='Отчеты по тапам готовы',
    ) as stage:
        try:
            tap_reward_report_service.set_bot(bot)
            await tap_reward_report_service.start()
        except Exception as error:
            warn_startup_stage_error(
                stage=stage,
                logger=logger,
                stage_error_message='Ошибка запуска отчетов по тапам',
                logger_error_message='❌ Ошибка запуска отчетов по тапам',
                error=error,
            )
