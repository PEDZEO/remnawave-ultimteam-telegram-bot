from dataclasses import dataclass

import structlog

from app.bootstrap.localization_startup import prepare_localizations
from app.bootstrap.runtime_logging import configure_runtime_logging
from app.bootstrap.types import TelegramNotifierLike
from app.config import settings
from app.logging_config import setup_logging
from app.utils.startup_timeline import StartupTimeline


@dataclass(slots=True)
class RuntimePreflightContext:
    logger: structlog.typing.FilteringBoundLogger
    timeline: StartupTimeline
    telegram_notifier: TelegramNotifierLike


def _validate_security_settings() -> None:
    if settings.CABINET_ENABLED and not settings.CABINET_JWT_SECRET:
        raise RuntimeError('CABINET_JWT_SECRET must be configured when CABINET_ENABLED=true')


def _build_preflight_banner_metadata() -> list[tuple[str, str]]:
    return [
        ('Уровень логирования', settings.LOG_LEVEL),
        ('Режим БД', settings.DATABASE_MODE),
    ]


def _build_preflight_runtime_objects() -> tuple[structlog.typing.FilteringBoundLogger, StartupTimeline]:
    logger = structlog.get_logger(__name__)
    timeline = StartupTimeline(logger, 'Bedolaga Remnawave Bot')
    return logger, timeline


async def prepare_runtime_preflight() -> RuntimePreflightContext:
    _validate_security_settings()
    file_formatter, console_formatter, telegram_notifier = setup_logging()
    await configure_runtime_logging(file_formatter, console_formatter)

    # NOTE: TelegramNotifierProcessor and noisy logger suppression are
    # handled inside setup_logging() / logging_config.py.
    logger, timeline = _build_preflight_runtime_objects()
    timeline.log_banner(_build_preflight_banner_metadata())
    await prepare_localizations(timeline, logger)

    return RuntimePreflightContext(
        logger=logger,
        timeline=timeline,
        telegram_notifier=telegram_notifier,
    )
