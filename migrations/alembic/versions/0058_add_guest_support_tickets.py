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
    ticket_indexes = _indexes('tickets')
    ticket_checks = _checks('tickets')
    # batch_alter_table is required for SQLite, which cannot add constraints or
    # change column nullability with ALTER TABLE. It emits regular ALTERs on
    # databases that support them.
    with op.batch_alter_table('tickets') as batch_op:
        if not ticket_columns['user_id']['nullable']:
            batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=True)
        if 'guest_name' not in ticket_columns:
            batch_op.add_column(sa.Column('guest_name', sa.String(length=120), nullable=True))
        if 'guest_contact' not in ticket_columns:
            batch_op.add_column(sa.Column('guest_contact', sa.String(length=255), nullable=True))
        if 'guest_token_hash' not in ticket_columns:
            batch_op.add_column(sa.Column('guest_token_hash', sa.String(length=64), nullable=True))
        if 'ix_tickets_user_id' not in ticket_indexes:
            batch_op.create_index('ix_tickets_user_id', ['user_id'], unique=False)
        if 'ix_tickets_guest_token_hash' not in ticket_indexes:
            batch_op.create_index('ix_tickets_guest_token_hash', ['guest_token_hash'], unique=True)
        if 'ck_tickets_owner_present' not in ticket_checks:
            batch_op.create_check_constraint(
                'ck_tickets_owner_present',
                'user_id IS NOT NULL OR guest_token_hash IS NOT NULL',
            )

    message_columns = _columns('ticket_messages')
    message_indexes = _indexes('ticket_messages')
    with op.batch_alter_table('ticket_messages') as batch_op:
        if not message_columns['user_id']['nullable']:
            batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=True)
        if 'ix_ticket_messages_user_id' not in message_indexes:
            batch_op.create_index('ix_ticket_messages_user_id', ['user_id'], unique=False)


def downgrade() -> None:
    # Guest tickets cannot satisfy the old non-null foreign keys. Removing them
    # makes the downgrade deterministic instead of failing midway.
    op.execute('DELETE FROM tickets WHERE user_id IS NULL')
    # SQLite does not enforce foreign keys unless PRAGMA foreign_keys is enabled,
    # so remove orphaned guest messages explicitly before restoring NOT NULL.
    op.execute('DELETE FROM ticket_messages WHERE user_id IS NULL')
    message_columns = _columns('ticket_messages')
    message_indexes = _indexes('ticket_messages')
    with op.batch_alter_table('ticket_messages') as batch_op:
        if 'ix_ticket_messages_user_id' in message_indexes:
            batch_op.drop_index('ix_ticket_messages_user_id')
        if message_columns['user_id']['nullable']:
            batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)

    ticket_indexes = _indexes('tickets')
    ticket_columns = _columns('tickets')
    ticket_checks = _checks('tickets')
    with op.batch_alter_table('tickets') as batch_op:
        if 'ck_tickets_owner_present' in ticket_checks:
            batch_op.drop_constraint('ck_tickets_owner_present', type_='check')
        if 'ix_tickets_guest_token_hash' in ticket_indexes:
            batch_op.drop_index('ix_tickets_guest_token_hash')
        if 'ix_tickets_user_id' in ticket_indexes:
            batch_op.drop_index('ix_tickets_user_id')
        for column_name in ('guest_token_hash', 'guest_contact', 'guest_name'):
            if column_name in ticket_columns:
                batch_op.drop_column(column_name)
        if ticket_columns['user_id']['nullable']:
            batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
