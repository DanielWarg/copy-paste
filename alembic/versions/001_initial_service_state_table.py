"""initial service state table

Revision ID: 001
Revises: 
Create Date: 2025-12-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'service_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_name', sa.String(), nullable=False),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('service_name')
    )


def downgrade() -> None:
    op.drop_table('service_state')

