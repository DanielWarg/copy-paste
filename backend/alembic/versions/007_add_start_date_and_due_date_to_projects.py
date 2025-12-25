"""Add start_date and due_date to projects.

Revision ID: 007
Revises: 006
Create Date: 2025-12-25

"""
from alembic import op
import sqlalchemy as sa
from datetime import date


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add start_date and due_date columns to projects table."""
    # Add start_date column (NOT NULL, default to today)
    op.add_column('projects', sa.Column('start_date', sa.Date(), nullable=False, server_default=sa.func.current_date()))
    op.add_column('projects', sa.Column('due_date', sa.Date(), nullable=True))
    
    # Create indexes
    op.create_index(op.f('ix_projects_start_date'), 'projects', ['start_date'], unique=False)
    op.create_index(op.f('ix_projects_due_date'), 'projects', ['due_date'], unique=False)


def downgrade() -> None:
    """Remove start_date and due_date columns from projects table."""
    op.drop_index(op.f('ix_projects_due_date'), table_name='projects')
    op.drop_index(op.f('ix_projects_start_date'), table_name='projects')
    op.drop_column('projects', 'due_date')
    op.drop_column('projects', 'start_date')

