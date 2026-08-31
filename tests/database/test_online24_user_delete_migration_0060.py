from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest


def _load_migration():
    migration_path = (
        Path(__file__).parents[2] / 'migrations/alembic/versions/0060_fix_online24_migration_user_delete.py'
    )
    spec = importlib.util.spec_from_file_location('migration_0060', migration_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Inspector:
    def __init__(self, *, has_table: bool, ondelete: str | None = None) -> None:
        self.has_table = has_table
        self.ondelete = ondelete

    def get_table_names(self) -> list[str]:
        return ['online24_migration_users'] if self.has_table else []

    def get_columns(self, _table: str) -> list[dict[str, str]]:
        return [{'name': 'destination_user_id'}]

    def get_foreign_keys(self, _table: str) -> list[dict[str, object]]:
        return [
            {
                'name': 'online24_migration_users_destination_user_id_fkey',
                'constrained_columns': ['destination_user_id'],
                'referred_table': 'users',
                'options': {'ondelete': self.ondelete} if self.ondelete else {},
            }
        ]


@pytest.mark.parametrize('has_table', [False, True])
def test_upgrade_is_safe_for_optional_online24_table(monkeypatch: pytest.MonkeyPatch, has_table: bool) -> None:
    migration = _load_migration()
    inspector = _Inspector(has_table=has_table)
    fake_op = Mock()
    fake_op.get_bind.return_value = object()
    migration.op = fake_op
    monkeypatch.setattr(migration.sa, 'inspect', lambda _bind: inspector)

    migration.upgrade()

    if has_table:
        fake_op.drop_constraint.assert_called_once_with(
            'online24_migration_users_destination_user_id_fkey',
            'online24_migration_users',
            type_='foreignkey',
        )
        fake_op.create_foreign_key.assert_called_once_with(
            'online24_migration_users_destination_user_id_fkey',
            'online24_migration_users',
            'users',
            ['destination_user_id'],
            ['id'],
            ondelete='CASCADE',
        )
    else:
        fake_op.drop_constraint.assert_not_called()
        fake_op.create_foreign_key.assert_not_called()
