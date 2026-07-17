"""add indexes for scalable metered traffic queries

Revision ID: 0057
Revises: 0056
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0057'
down_revision: str | None = '0056'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_INDEXES = {
    'ix_subscriptions_status_end_date': ['status', 'end_date'],
    'ix_subscriptions_metered_blocked_at': [
        'metered_access_blocked',
        'metered_access_blocked_at',
    ],
}


def _existing_indexes() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index['name'] for index in inspector.get_indexes('subscriptions')}


def upgrade() -> None:
    existing = _existing_indexes()
    for name, columns in _INDEXES.items():
        if name not in existing:
            op.create_index(name, 'subscriptions', columns, unique=False)


def downgrade() -> None:
    existing = _existing_indexes()
    for name in reversed(_INDEXES):
        if name in existing:
            op.drop_index(name, table_name='subscriptions')
