"""allow deleting users created by the Online24 migration

Revision ID: 0060
Revises: 0059
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0060'
down_revision: str | None = '0059'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = 'online24_migration_users'
_COLUMN = 'destination_user_id'
_FK_NAME = 'online24_migration_users_destination_user_id_fkey'


def _destination_user_fk() -> dict[str, object] | None:
    inspector = sa.inspect(op.get_bind())
    if _TABLE not in inspector.get_table_names():
        return None
    if _COLUMN not in {column['name'] for column in inspector.get_columns(_TABLE)}:
        return None

    for foreign_key in inspector.get_foreign_keys(_TABLE):
        if foreign_key.get('constrained_columns') == [_COLUMN] and foreign_key.get('referred_table') == 'users':
            return foreign_key
    return None


def _replace_fk(ondelete: str | None) -> None:
    foreign_key = _destination_user_fk()
    if foreign_key is None:
        return

    current_ondelete = (foreign_key.get('options') or {}).get('ondelete')
    if current_ondelete == ondelete:
        return

    constraint_name = foreign_key.get('name')
    if constraint_name:
        op.drop_constraint(str(constraint_name), _TABLE, type_='foreignkey')
    op.create_foreign_key(
        _FK_NAME,
        _TABLE,
        'users',
        [_COLUMN],
        ['id'],
        ondelete=ondelete,
    )


def upgrade() -> None:
    _replace_fk('CASCADE')


def downgrade() -> None:
    _replace_fk(None)
