import asyncio
import shutil
from pathlib import Path

import pytest

from app.services.backup_service import BackupService


pytestmark = pytest.mark.asyncio


async def test_create_backup_recreates_deleted_backup_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    service = BackupService()
    service.backup_dir = tmp_path / 'backups'
    service.data_dir = tmp_path
    service.backup_dir.mkdir()
    shutil.rmtree(service.backup_dir)

    async def collect_database_overview():
        return {'tables_count': 1, 'total_records': 2}

    async def dump_database(staging_dir: Path, include_logs: bool):
        (staging_dir / 'database.json').write_text('{}', encoding='utf-8')
        return {'type': 'postgresql', 'tables_count': 1, 'total_records': 2}

    async def collect_files(staging_dir: Path, include_logs: bool):
        return {}

    async def collect_data_snapshot(staging_dir: Path):
        return {}

    async def cleanup_old_backups():
        return None

    monkeypatch.setattr(service, '_collect_database_overview', collect_database_overview)
    monkeypatch.setattr(service, '_dump_database', dump_database)
    monkeypatch.setattr(service, '_collect_files', collect_files)
    monkeypatch.setattr(service, '_collect_data_snapshot', collect_data_snapshot)
    monkeypatch.setattr(service, '_cleanup_old_backups', cleanup_old_backups)

    success, _, backup_path = await service.create_backup(created_by=1)

    assert success is True
    assert backup_path is not None
    assert await asyncio.to_thread(Path(backup_path).is_file)
