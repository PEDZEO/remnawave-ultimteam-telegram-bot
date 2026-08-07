from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _load_migration() -> ModuleType:
    path = (
        Path(__file__).resolve().parents[2]
        / 'migrations'
        / 'alembic'
        / 'versions'
        / '0059_add_user_activity_and_ticket_message_indexes.py'
    )
    spec = importlib.util.spec_from_file_location('migration_0059_scaling_indexes', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeInspector:
    def __init__(self, indexes: dict[str, set[str]]) -> None:
        self.indexes = indexes

    def get_indexes(self, table_name: str) -> list[dict[str, str]]:
        return [{'name': name} for name in self.indexes.get(table_name, set())]


class FakeOp:
    def __init__(self, indexes: dict[str, set[str]]) -> None:
        self.indexes = indexes
        self.created: list[tuple[str, str, tuple[str, ...]]] = []

    def get_bind(self) -> object:
        return object()

    def create_index(self, name: str, table: str, columns: list[str], *, unique: bool) -> None:
        if name in self.indexes.setdefault(table, set()):
            raise AssertionError(f'duplicate index: {name}')
        assert unique is False
        self.indexes[table].add(name)
        self.created.append((name, table, tuple(columns)))


def test_upgrade_creates_only_missing_indexes(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_migration()
    indexes = {'users': {'ix_users_status_last_activity'}, 'ticket_messages': set()}
    fake_op = FakeOp(indexes)
    monkeypatch.setattr(module, 'op', fake_op)
    monkeypatch.setattr(module.sa, 'inspect', lambda _bind: FakeInspector(indexes))

    module.upgrade()

    assert fake_op.created == [
        ('ix_ticket_messages_ticket_created', 'ticket_messages', ('ticket_id', 'created_at')),
    ]
