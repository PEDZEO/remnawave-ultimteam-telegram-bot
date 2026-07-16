"""add traffic bonus for additional devices

Revision ID: 0056
Revises: 0055
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0056'
down_revision: str | None = '0055'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column['name'] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_column('tariffs', 'device_traffic_gb'):
        op.add_column(
            'tariffs',
            sa.Column('device_traffic_gb', sa.Integer(), nullable=False, server_default='0'),
        )

    if not _has_column('subscriptions', 'device_bonus_traffic_gb'):
        op.add_column(
            'subscriptions',
            sa.Column('device_bonus_traffic_gb', sa.Integer(), nullable=False, server_default='0'),
        )


def downgrade() -> None:
    if _has_column('subscriptions', 'device_bonus_traffic_gb'):
        op.drop_column('subscriptions', 'device_bonus_traffic_gb')
    if _has_column('tariffs', 'device_traffic_gb'):
        op.drop_column('tariffs', 'device_traffic_gb')
