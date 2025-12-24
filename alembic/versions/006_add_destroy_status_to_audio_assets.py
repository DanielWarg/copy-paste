"""Add destroy_status and destroyed_at to audio_assets.

Revision ID: 006
Revises: 005
Create Date: 2025-12-23 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add destroy_status and destroyed_at columns."""
    op.add_column('audio_assets', sa.Column('destroy_status', sa.String(), nullable=False, server_default='none'))
    op.add_column('audio_assets', sa.Column('destroyed_at', sa.DateTime(), nullable=True))
    op.create_index('ix_audio_assets_destroy_status', 'audio_assets', ['destroy_status'], unique=False)


def downgrade() -> None:
    """Remove destroy_status and destroyed_at columns."""
    op.drop_index('ix_audio_assets_destroy_status', table_name='audio_assets')
    op.drop_column('audio_assets', 'destroyed_at')
    op.drop_column('audio_assets', 'destroy_status')

