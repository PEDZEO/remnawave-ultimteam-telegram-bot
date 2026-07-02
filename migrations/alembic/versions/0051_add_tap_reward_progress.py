"""add tap reward progress

Revision ID: 0051
Revises: 0050
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0051'
down_revision: str | None = '0050'
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


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return index_name in {index['name'] for index in _inspector().get_indexes(table_name)}


def _has_unique_constraint(table_name: str, constraint_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return constraint_name in {constraint['name'] for constraint in _inspector().get_unique_constraints(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _has_column(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    if not _has_table('tap_reward_progress'):
        op.create_table(
            'tap_reward_progress',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('total_taps', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('reward_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('daily_reward_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('daily_reward_date', sa.Date(), nullable=True),
            sa.Column('last_tap_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_reward_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint('user_id', name='uq_tap_reward_progress_user_id'),
        )
    else:
        _add_column_if_missing(
            'tap_reward_progress',
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        )
        _add_column_if_missing(
            'tap_reward_progress',
            sa.Column('total_taps', sa.Integer(), nullable=False, server_default='0'),
        )
        _add_column_if_missing(
            'tap_reward_progress',
            sa.Column('reward_count', sa.Integer(), nullable=False, server_default='0'),
        )
        _add_column_if_missing(
            'tap_reward_progress',
            sa.Column('daily_reward_count', sa.Integer(), nullable=False, server_default='0'),
        )
        _add_column_if_missing('tap_reward_progress', sa.Column('daily_reward_date', sa.Date(), nullable=True))
        _add_column_if_missing('tap_reward_progress', sa.Column('last_tap_at', sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(
            'tap_reward_progress',
            sa.Column('last_reward_at', sa.DateTime(timezone=True), nullable=True),
        )
        _add_column_if_missing(
            'tap_reward_progress',
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        _add_column_if_missing(
            'tap_reward_progress',
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

        if not _has_unique_constraint('tap_reward_progress', 'uq_tap_reward_progress_user_id'):
            op.create_unique_constraint(
                'uq_tap_reward_progress_user_id',
                'tap_reward_progress',
                ['user_id'],
            )

    if not _has_index('tap_reward_progress', 'ix_tap_reward_progress_user_id'):
        op.create_index('ix_tap_reward_progress_user_id', 'tap_reward_progress', ['user_id'])


def downgrade() -> None:
    if _has_table('tap_reward_progress'):
        op.drop_table('tap_reward_progress')
