"""add guest support tickets

Revision ID: 0058
Revises: 0057
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0058'
down_revision: str | None = '0057'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _columns(table_name: str) -> dict[str, dict]:
    return {column['name']: column for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _indexes(table_name: str) -> set[str]:
    return {index['name'] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def _checks(table_name: str) -> set[str]:
    return {
        constraint['name']
        for constraint in sa.inspect(op.get_bind()).get_check_constraints(table_name)
        if constraint.get('name')
    }


def upgrade() -> None:
    ticket_columns = _columns('tickets')
    if not ticket_columns['user_id']['nullable']:
        op.alter_column('tickets', 'user_id', existing_type=sa.Integer(), nullable=True)
    if 'guest_name' not in ticket_columns:
        op.add_column('tickets', sa.Column('guest_name', sa.String(length=120), nullable=True))
    if 'guest_contact' not in ticket_columns:
        op.add_column('tickets', sa.Column('guest_contact', sa.String(length=255), nullable=True))
    if 'guest_token_hash' not in ticket_columns:
        op.add_column('tickets', sa.Column('guest_token_hash', sa.String(length=64), nullable=True))

    ticket_indexes = _indexes('tickets')
    if 'ix_tickets_user_id' not in ticket_indexes:
        op.create_index('ix_tickets_user_id', 'tickets', ['user_id'], unique=False)
    if 'ix_tickets_guest_token_hash' not in ticket_indexes:
        op.create_index('ix_tickets_guest_token_hash', 'tickets', ['guest_token_hash'], unique=True)

    message_columns = _columns('ticket_messages')
    if not message_columns['user_id']['nullable']:
        op.alter_column('ticket_messages', 'user_id', existing_type=sa.Integer(), nullable=True)
    if 'ix_ticket_messages_user_id' not in _indexes('ticket_messages'):
        op.create_index('ix_ticket_messages_user_id', 'ticket_messages', ['user_id'], unique=False)

    if 'ck_tickets_owner_present' not in _checks('tickets'):
        op.create_check_constraint(
            'ck_tickets_owner_present',
            'tickets',
            'user_id IS NOT NULL OR guest_token_hash IS NOT NULL',
        )


def downgrade() -> None:
    # Guest tickets cannot satisfy the old non-null foreign keys. Removing them
    # makes the downgrade deterministic instead of failing midway.
    op.execute("DELETE FROM tickets WHERE user_id IS NULL")
    if 'ck_tickets_owner_present' in _checks('tickets'):
        op.drop_constraint('ck_tickets_owner_present', 'tickets', type_='check')
    if 'ix_ticket_messages_user_id' in _indexes('ticket_messages'):
        op.drop_index('ix_ticket_messages_user_id', table_name='ticket_messages')
    if _columns('ticket_messages')['user_id']['nullable']:
        op.alter_column('ticket_messages', 'user_id', existing_type=sa.Integer(), nullable=False)

    ticket_indexes = _indexes('tickets')
    if 'ix_tickets_guest_token_hash' in ticket_indexes:
        op.drop_index('ix_tickets_guest_token_hash', table_name='tickets')
    if 'ix_tickets_user_id' in ticket_indexes:
        op.drop_index('ix_tickets_user_id', table_name='tickets')
    ticket_columns = _columns('tickets')
    for column_name in ('guest_token_hash', 'guest_contact', 'guest_name'):
        if column_name in ticket_columns:
            op.drop_column('tickets', column_name)
    if _columns('tickets')['user_id']['nullable']:
        op.alter_column('tickets', 'user_id', existing_type=sa.Integer(), nullable=False)
