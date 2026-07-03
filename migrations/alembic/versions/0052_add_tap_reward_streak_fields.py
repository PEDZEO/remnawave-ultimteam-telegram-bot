"""add tap reward streak fields

Revision ID: 0052
Revises: 0051
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0052'
down_revision: str | None = '0051'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return column_name in {column['name'] for column in _inspector().get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _has_column(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    if not _has_table('tap_reward_progress'):
        return

    _add_column_if_missing(
        'tap_reward_progress',
        sa.Column('streak_taps', sa.Integer(), nullable=False, server_default='0'),
    )
    _add_column_if_missing(
        'tap_reward_progress',
        sa.Column('streak_reward_count', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    if not _has_table('tap_reward_progress'):
        return

    if _has_column('tap_reward_progress', 'streak_reward_count'):
        op.drop_column('tap_reward_progress', 'streak_reward_count')
    if _has_column('tap_reward_progress', 'streak_taps'):
        op.drop_column('tap_reward_progress', 'streak_taps')
