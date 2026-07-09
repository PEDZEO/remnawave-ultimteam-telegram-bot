"""Programmatic Alembic migration runner for bot startup."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import structlog
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text


logger = structlog.get_logger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ALEMBIC_INI = _PROJECT_ROOT / 'alembic.ini'
_MIGRATION_ADVISORY_LOCK_ID = 7_612_946_175_504_209_051
_migration_process_lock = asyncio.Lock()


@asynccontextmanager
async def _migration_execution_lock() -> AsyncIterator[None]:
    """Serialize schema changes across tasks and PostgreSQL application instances."""
    from app.database.database import IS_SQLITE, engine

    async with _migration_process_lock:
        if IS_SQLITE:
            yield
            return

        async with engine.connect() as conn:
            await conn.execute(
                text('SELECT pg_advisory_lock(:lock_id)'),
                {'lock_id': _MIGRATION_ADVISORY_LOCK_ID},
            )
            logger.info('Acquired PostgreSQL migration advisory lock')
            try:
                yield
            finally:
                try:
                    await conn.execute(
                        text('SELECT pg_advisory_unlock(:lock_id)'),
                        {'lock_id': _MIGRATION_ADVISORY_LOCK_ID},
                    )
                except Exception:
                    logger.exception('Failed to release PostgreSQL migration advisory lock')


def _get_alembic_config() -> Config:
    """Build Alembic Config pointing at the project root."""
    from app.config import settings

    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option('sqlalchemy.url', settings.get_database_url())
    return cfg


async def _run_alembic_command(func: Any, cfg: Config, *args: Any) -> None:
    """Run blocking Alembic command in thread executor."""
    loop = asyncio.get_running_loop()
    # Offload to thread where env.py can safely call asyncio.run() for its own loop.
    await loop.run_in_executor(None, func, cfg, *args)


async def _needs_auto_stamp() -> bool:
    """Check if DB has existing tables but no alembic_version (transition from universal_migration)."""
    from app.database.database import engine

    async with engine.connect() as conn:
        has_alembic = await _has_public_table(conn, 'alembic_version')
        if has_alembic:
            return False
        has_users = await _has_public_table(conn, 'users')
        return has_users


async def _is_fresh_database() -> bool:
    """Return True when the target DB has no public tables and no Alembic state."""
    from app.database.database import engine

    async with engine.connect() as conn:
        has_alembic = await _has_public_table(conn, 'alembic_version')
        if has_alembic:
            return False

        has_any_tables = await _has_any_public_tables(conn)
        return not has_any_tables


async def _is_current_schema_snapshot_without_alembic() -> bool:
    """Detect partially bootstrapped/current-schema DBs that should be stamped at head."""
    from app.database.database import engine

    async with engine.connect() as conn:
        has_alembic = await _has_public_table(conn, 'alembic_version')
        if has_alembic:
            return False

        return await _has_any_public_table(conn, ['guest_purchases', 'cabinet_refresh_tokens', 'main_menu_buttons'])


async def _bootstrap_current_schema() -> None:
    """Create the current SQLAlchemy metadata for a fresh database."""
    from app.database.database import engine
    from app.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(bind=sync_conn, checkfirst=True))

    logger.info('Current SQLAlchemy schema bootstrapped for fresh database')


_INITIAL_REVISION = '0001'
_LEGACY_REVISION_REMAP: dict[str, str] = {
    # Legacy branch value from older server snapshots no longer present in new chain.
    '0004': '0003',
    # Legacy post-0040 revisions were later squashed out of the current branch.
    # Production snapshots may still be stamped with these values even though the
    # current metadata already works with the resulting schema.
    '0041': '0040',
    '0042': '0040',
    '0043': '0040',
    '0044': '0040',
    '0045': '0040',
}


async def _has_public_table(conn, table_name: str) -> bool:
    """Check table existence via information_schema to avoid inspector false negatives."""
    query = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = :table_name
        )
        """
    )
    return bool((await conn.execute(query, {'table_name': table_name})).scalar())


async def _has_any_public_tables(conn) -> bool:
    """Check whether the public schema already contains any tables."""
    query = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
        )
        """
    )
    return bool((await conn.execute(query)).scalar())


async def _has_any_public_table(conn, table_names: list[str]) -> bool:
    """Check whether any table from the provided list exists in the public schema."""
    query = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = ANY(:table_names)
        )
        """
    )
    return bool((await conn.execute(query, {'table_names': table_names})).scalar())


async def _get_current_alembic_revision(conn) -> str | None:
    """Return current revision from alembic_version table, if present."""
    revision = (
        await conn.execute(text('SELECT version_num FROM alembic_version ORDER BY version_num LIMIT 1'))
    ).scalar_one_or_none()
    if revision is None:
        return None
    return str(revision)


async def _get_current_alembic_revisions(conn) -> list[str]:
    """Return all current Alembic revisions from alembic_version table."""
    result = await conn.execute(text('SELECT version_num FROM alembic_version ORDER BY version_num'))
    return [str(row[0]) for row in result.fetchall()]


async def _remap_legacy_revision_if_needed() -> bool:
    """Rewrite known obsolete alembic_version values to current chain nodes."""
    from app.database.database import engine

    async with engine.begin() as conn:
        has_alembic = await _has_public_table(conn, 'alembic_version')
        if not has_alembic:
            return False

        current_revisions = await _get_current_alembic_revisions(conn)
        if not current_revisions:
            return False

        current_revision_set = set(current_revisions)
        remapped_revisions: list[tuple[str, str]] = []

        for current_revision in current_revisions:
            target_revision = _LEGACY_REVISION_REMAP.get(current_revision)
            if target_revision is None or target_revision == current_revision:
                continue

            if target_revision in current_revision_set:
                await conn.execute(
                    text('DELETE FROM alembic_version WHERE version_num = :current'),
                    {'current': current_revision},
                )
            else:
                await conn.execute(
                    text('UPDATE alembic_version SET version_num = :target WHERE version_num = :current'),
                    {'target': target_revision, 'current': current_revision},
                )
                current_revision_set.remove(current_revision)
                current_revision_set.add(target_revision)

            remapped_revisions.append((current_revision, target_revision))

        if not remapped_revisions:
            return False

    logger.warning(
        'Alembic revision remap applied for legacy database snapshot',
        revisions=remapped_revisions,
    )
    return True


def _is_revision_ancestor(script: ScriptDirectory, ancestor_revision: str, descendant_revision: str) -> bool:
    """Return True when ``ancestor_revision`` is in the lineage of ``descendant_revision``."""
    if ancestor_revision == descendant_revision:
        return False

    try:
        return any(
            revision.revision == ancestor_revision
            for revision in script.walk_revisions(base='base', head=descendant_revision)
        )
    except Exception:
        return False


async def _normalize_overlapping_current_revisions_if_needed() -> bool:
    """Remove legacy ancestor rows when alembic_version contains overlapping current revisions."""
    from app.database.database import engine

    async with engine.begin() as conn:
        has_alembic = await _has_public_table(conn, 'alembic_version')
        if not has_alembic:
            return False

        current_revisions = await _get_current_alembic_revisions(conn)
        if len(current_revisions) < 2:
            return False

        script = ScriptDirectory.from_config(_get_alembic_config())
        ancestor_revisions = sorted(
            {
                revision
                for revision in current_revisions
                for other_revision in current_revisions
                if revision != other_revision and _is_revision_ancestor(script, revision, other_revision)
            }
        )
        if not ancestor_revisions:
            return False

        await conn.execute(
            text('DELETE FROM alembic_version WHERE version_num = ANY(:revisions)'),
            {'revisions': ancestor_revisions},
        )

    logger.warning(
        'Removed overlapping ancestor revisions from alembic_version',
        revisions=ancestor_revisions,
    )
    return True


async def run_alembic_upgrade() -> None:
    """Run ``alembic upgrade heads``, auto-stamping existing databases first."""
    async with _migration_execution_lock():
        await _run_alembic_upgrade_locked()


async def _run_alembic_upgrade_locked() -> None:
    """Run schema bootstrap and Alembic while the global migration lock is held."""
    await _remap_legacy_revision_if_needed()
    await _normalize_overlapping_current_revisions_if_needed()

    if await _is_fresh_database():
        logger.warning('Fresh database detected — bootstrapping current schema and stamping Alembic heads')
        await _bootstrap_current_schema()
        await _stamp_alembic_revision('heads')
        return

    if await _is_current_schema_snapshot_without_alembic():
        logger.warning('Current-schema database without alembic_version detected — stamping Alembic heads')
        await _stamp_alembic_revision('heads')
        return

    if await _needs_auto_stamp():
        logger.warning(
            'Обнаружена существующая БД без alembic_version — автоматический stamp 0001 (переход с universal_migration)'
        )
        await _stamp_alembic_revision(_INITIAL_REVISION)

    cfg = _get_alembic_config()
    await _run_alembic_command(command.upgrade, cfg, 'heads')
    logger.info('Alembic миграции применены')


async def stamp_alembic_head() -> None:
    """Stamp the DB as being at head without running migrations (for existing DBs)."""
    await _stamp_alembic_revision('heads')


async def _stamp_alembic_revision(revision: str) -> None:
    """Stamp the DB at a specific revision without running migrations."""
    cfg = _get_alembic_config()
    await _run_alembic_command(command.stamp, cfg, revision)
    logger.info('Alembic: база отмечена как актуальная', revision=revision)
