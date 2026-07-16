"""add tariff-level special server access

Revision ID: 0055
Revises: 0054
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0055'
down_revision: str | None = '0054'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column['name'] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if _has_column('tariffs', 'special_servers_enabled'):
        return

    op.add_column(
        'tariffs',
        sa.Column(
            'special_servers_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    # Preserve the current rollout for existing plans. New plans stay opt-in.
    op.execute(sa.text('UPDATE tariffs SET special_servers_enabled = true'))


def downgrade() -> None:
    if _has_column('tariffs', 'special_servers_enabled'):
        op.drop_column('tariffs', 'special_servers_enabled')
