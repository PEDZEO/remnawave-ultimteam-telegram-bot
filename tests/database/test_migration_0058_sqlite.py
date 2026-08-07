import importlib.util
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


def _load_migration():
    migration_path = Path(__file__).parents[2] / 'migrations/alembic/versions/0058_add_guest_support_tickets.py'
    spec = importlib.util.spec_from_file_location('migration_0058', migration_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sqlite_engine():
    engine = create_engine('sqlite://')
    try:
        yield engine
    finally:
        engine.dispose()


def test_guest_support_migration_upgrades_sqlite_schema(sqlite_engine) -> None:
    engine = sqlite_engine
    migration = _load_migration()

    with engine.begin() as connection:
        connection.execute(
            text('CREATE TABLE tickets (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, title TEXT NOT NULL)')
        )
        connection.execute(
            text(
                'CREATE TABLE ticket_messages (id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL, user_id INTEGER NOT NULL)'
            )
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

        inspector = inspect(connection)
        ticket_columns = {column['name']: column for column in inspector.get_columns('tickets')}
        message_columns = {column['name']: column for column in inspector.get_columns('ticket_messages')}

        assert ticket_columns['user_id']['nullable'] is True
        assert ticket_columns['guest_name']['nullable'] is True
        assert ticket_columns['guest_contact']['nullable'] is True
        assert ticket_columns['guest_token_hash']['nullable'] is True
        assert message_columns['user_id']['nullable'] is True
        assert 'ck_tickets_owner_present' in {
            constraint['name'] for constraint in inspector.get_check_constraints('tickets')
        }


def test_guest_support_migration_downgrades_sqlite_schema(sqlite_engine) -> None:
    engine = sqlite_engine
    migration = _load_migration()

    with engine.begin() as connection:
        connection.execute(
            text('CREATE TABLE tickets (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, title TEXT NOT NULL)')
        )
        connection.execute(
            text(
                'CREATE TABLE ticket_messages (id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL, user_id INTEGER NOT NULL)'
            )
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        connection.execute(
            text(
                'INSERT INTO tickets (id, user_id, guest_name, guest_token_hash, title) '
                "VALUES (1, NULL, 'Guest', 'token-hash', 'Support')"
            )
        )
        connection.execute(text('INSERT INTO ticket_messages (id, ticket_id, user_id) VALUES (1, 1, NULL)'))

        migration.op = Operations(MigrationContext.configure(connection))
        migration.downgrade()

        inspector = inspect(connection)
        ticket_columns = {column['name']: column for column in inspector.get_columns('tickets')}
        message_columns = {column['name']: column for column in inspector.get_columns('ticket_messages')}

        assert ticket_columns['user_id']['nullable'] is False
        assert message_columns['user_id']['nullable'] is False
        assert 'guest_token_hash' not in ticket_columns
