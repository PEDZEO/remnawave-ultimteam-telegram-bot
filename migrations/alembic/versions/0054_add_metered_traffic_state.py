"""add metered traffic state

Revision ID: 0054
Revises: 0053
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0054'
down_revision: str | None = '0053'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_column(table_name: str, column_name: str) -> bool:
    return column_name in {column['name'] for column in _inspector().get_columns(table_name)}


def _add_column_if_missing(column: sa.Column) -> None:
    if not _has_column('subscriptions', column.name):
        op.add_column('subscriptions', column)


def upgrade() -> None:
    _add_column_if_missing(
        sa.Column('metered_traffic_baseline_bytes', sa.BigInteger(), nullable=False, server_default='0')
    )
    _add_column_if_missing(
        sa.Column('metered_traffic_last_counter_bytes', sa.BigInteger(), nullable=False, server_default='0')
    )
    _add_column_if_missing(sa.Column('metered_traffic_initialized_at', sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing(sa.Column('metered_traffic_last_checked_at', sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing(
        sa.Column('metered_access_blocked', sa.Boolean(), nullable=False, server_default=sa.false())
    )
    _add_column_if_missing(sa.Column('metered_access_blocked_at', sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing(sa.Column('metered_warning_percent', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    for column_name in (
        'metered_warning_percent',
        'metered_access_blocked_at',
        'metered_access_blocked',
        'metered_traffic_last_checked_at',
        'metered_traffic_initialized_at',
        'metered_traffic_last_counter_bytes',
        'metered_traffic_baseline_bytes',
    ):
        if _has_column('subscriptions', column_name):
            op.drop_column('subscriptions', column_name)
