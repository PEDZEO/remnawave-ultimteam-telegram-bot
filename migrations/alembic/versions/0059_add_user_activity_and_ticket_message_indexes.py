"""add user activity and ticket message indexes

Revision ID: 0059
Revises: 0058
Create Date: 2026-08-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0059'
down_revision: str | None = '0058'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _indexes(table_name: str) -> set[str]:
    return {index['name'] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    user_indexes = _indexes('users')
    if 'ix_users_status_last_activity' not in user_indexes:
        op.create_index(
            'ix_users_status_last_activity',
            'users',
            ['status', 'last_activity'],
            unique=False,
        )

    message_indexes = _indexes('ticket_messages')
    if 'ix_ticket_messages_ticket_created' not in message_indexes:
        op.create_index(
            'ix_ticket_messages_ticket_created',
            'ticket_messages',
            ['ticket_id', 'created_at'],
            unique=False,
        )


def downgrade() -> None:
    message_indexes = _indexes('ticket_messages')
    if 'ix_ticket_messages_ticket_created' in message_indexes:
        op.drop_index('ix_ticket_messages_ticket_created', table_name='ticket_messages')

    user_indexes = _indexes('users')
    if 'ix_users_status_last_activity' in user_indexes:
        op.drop_index('ix_users_status_last_activity', table_name='users')
