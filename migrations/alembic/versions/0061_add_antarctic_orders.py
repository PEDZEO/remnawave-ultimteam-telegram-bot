"""Store Antarctic Wallet payments and their subscription deliveries."""

import sqlalchemy as sa
from alembic import op


revision = '0061'
down_revision = '0060'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'antarctic_orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('owner', sa.String(64), nullable=False),
        sa.Column('amount', sa.String(24), nullable=False),
        sa.Column('plan_name', sa.String(255), nullable=False),
        sa.Column('days', sa.Integer(), nullable=False),
        sa.Column('device_limit', sa.Integer(), nullable=False),
        sa.Column('plan_config', sa.JSON(), nullable=False),
        sa.Column('operation_id', sa.String(36), unique=True),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('subscription_url', sa.Text()),
    )
    op.create_index('ix_antarctic_orders_owner_created', 'antarctic_orders', ['owner', 'created_at'])


def downgrade() -> None:
    op.drop_table('antarctic_orders')
