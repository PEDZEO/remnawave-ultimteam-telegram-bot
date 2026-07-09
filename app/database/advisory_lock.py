"""Cross-process PostgreSQL advisory locks for singleton background jobs."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from sqlalchemy import text


logger = structlog.get_logger(__name__)
_process_locks: dict[int, asyncio.Lock] = {}


@asynccontextmanager
async def distributed_job_lock(lock_id: int, *, name: str) -> AsyncIterator[bool]:
    """Try to acquire a process and PostgreSQL session lock without waiting."""
    from app.database.database import IS_SQLITE, engine

    process_lock = _process_locks.setdefault(lock_id, asyncio.Lock())
    if process_lock.locked():
        logger.info('Background job already runs in this process', job=name)
        yield False
        return

    await process_lock.acquire()
    try:
        if IS_SQLITE:
            yield True
            return

        async with engine.connect() as conn:
            acquired = bool(
                (
                    await conn.execute(
                        text('SELECT pg_try_advisory_lock(:lock_id)'),
                        {'lock_id': lock_id},
                    )
                ).scalar()
            )
            if not acquired:
                logger.info('Background job already runs in another instance', job=name)
                yield False
                return

            try:
                yield True
            finally:
                try:
                    await conn.execute(
                        text('SELECT pg_advisory_unlock(:lock_id)'),
                        {'lock_id': lock_id},
                    )
                except Exception:
                    logger.exception('Failed to release background job advisory lock', job=name)
                    await conn.invalidate()
    finally:
        process_lock.release()
