"""add tap reward daily stats

Revision ID: 0053
Revises: 0052
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0053'
down_revision: str | None = '0052'
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
    if not _has_table('tap_reward_daily_stats'):
        op.create_table(
            'tap_reward_daily_stats',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('stat_date', sa.Date(), nullable=False),
            sa.Column('tap_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('reward_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('balance_reward_kopeks', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('subscription_reward_days', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('last_tap_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_reward_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint('user_id', 'stat_date', name='uq_tap_reward_daily_stats_user_date'),
        )
    else:
        _add_column_if_missing(
            'tap_reward_daily_stats',
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        )
        _add_column_if_missing('tap_reward_daily_stats', sa.Column('stat_date', sa.Date(), nullable=False))
        _add_column_if_missing(
            'tap_reward_daily_stats',
            sa.Column('tap_count', sa.Integer(), nullable=False, server_default='0'),
        )
        _add_column_if_missing(
            'tap_reward_daily_stats',
            sa.Column('reward_count', sa.Integer(), nullable=False, server_default='0'),
        )
        _add_column_if_missing(
            'tap_reward_daily_stats',
            sa.Column('balance_reward_kopeks', sa.Integer(), nullable=False, server_default='0'),
        )
        _add_column_if_missing(
            'tap_reward_daily_stats',
            sa.Column('subscription_reward_days', sa.Integer(), nullable=False, server_default='0'),
        )
        _add_column_if_missing('tap_reward_daily_stats', sa.Column('last_tap_at', sa.DateTime(timezone=True), nullable=True))
        _add_column_if_missing(
            'tap_reward_daily_stats',
            sa.Column('last_reward_at', sa.DateTime(timezone=True), nullable=True),
        )
        _add_column_if_missing(
            'tap_reward_daily_stats',
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        _add_column_if_missing(
            'tap_reward_daily_stats',
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

        if not _has_unique_constraint('tap_reward_daily_stats', 'uq_tap_reward_daily_stats_user_date'):
            op.create_unique_constraint(
                'uq_tap_reward_daily_stats_user_date',
                'tap_reward_daily_stats',
                ['user_id', 'stat_date'],
            )

    if not _has_index('tap_reward_daily_stats', 'ix_tap_reward_daily_stats_date'):
        op.create_index('ix_tap_reward_daily_stats_date', 'tap_reward_daily_stats', ['stat_date'])
    if not _has_index('tap_reward_daily_stats', 'ix_tap_reward_daily_stats_user_id'):
        op.create_index('ix_tap_reward_daily_stats_user_id', 'tap_reward_daily_stats', ['user_id'])


def downgrade() -> None:
    if _has_table('tap_reward_daily_stats'):
        op.drop_table('tap_reward_daily_stats')
