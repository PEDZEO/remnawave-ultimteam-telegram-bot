from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.bootstrap import runtime_preflight


def test_build_preflight_banner_metadata_uses_settings_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        runtime_preflight,
        'settings',
        SimpleNamespace(LOG_LEVEL='DEBUG', DATABASE_MODE='sqlite'),
    )

    metadata = runtime_preflight._build_preflight_banner_metadata()

    assert metadata == [
        ('Уровень логирования', 'DEBUG'),
        ('Режим БД', 'sqlite'),
    ]


def test_build_preflight_runtime_objects_creates_logger_and_timeline(monkeypatch: pytest.MonkeyPatch) -> None:
    logger = MagicMock()
    timeline = MagicMock()
    get_logger = MagicMock(return_value=logger)
    startup_timeline_cls = MagicMock(return_value=timeline)
    monkeypatch.setattr(runtime_preflight.structlog, 'get_logger', get_logger)
    monkeypatch.setattr(runtime_preflight, 'StartupTimeline', startup_timeline_cls)

    built_logger, built_timeline = runtime_preflight._build_preflight_runtime_objects()

    assert built_logger is logger
    assert built_timeline is timeline
    get_logger.assert_called_once()
    startup_timeline_cls.assert_called_once_with(logger, 'Bedolaga Remnawave Bot')


def test_security_settings_require_dedicated_cabinet_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        runtime_preflight,
        'settings',
        SimpleNamespace(CABINET_ENABLED=True, CABINET_JWT_SECRET=None),
    )

    with pytest.raises(RuntimeError, match='CABINET_JWT_SECRET'):
        runtime_preflight._validate_security_settings()


@pytest.mark.asyncio
async def test_prepare_runtime_preflight_logs_banner_from_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    logger = MagicMock()
    timeline = MagicMock()
    telegram_notifier = object()
    validate_security_settings = MagicMock()
    monkeypatch.setattr(runtime_preflight, '_validate_security_settings', validate_security_settings)

    monkeypatch.setattr(
        runtime_preflight,
        'setup_logging',
        lambda: ('file_formatter', 'console_formatter', telegram_notifier),
    )
    configure_runtime_logging = AsyncMock()
    monkeypatch.setattr(runtime_preflight, 'configure_runtime_logging', configure_runtime_logging)
    monkeypatch.setattr(runtime_preflight, '_build_preflight_runtime_objects', lambda: (logger, timeline))
    prepare_localizations = AsyncMock()
    monkeypatch.setattr(runtime_preflight, 'prepare_localizations', prepare_localizations)
    metadata = [('k', 'v')]
    monkeypatch.setattr(runtime_preflight, '_build_preflight_banner_metadata', lambda: metadata)

    result = await runtime_preflight.prepare_runtime_preflight()

    validate_security_settings.assert_called_once_with()
    configure_runtime_logging.assert_awaited_once_with('file_formatter', 'console_formatter')
    timeline.log_banner.assert_called_once_with(metadata)
    prepare_localizations.assert_awaited_once_with(timeline, logger)
    assert result.logger is logger
    assert result.timeline is timeline
    assert result.telegram_notifier is telegram_notifier
