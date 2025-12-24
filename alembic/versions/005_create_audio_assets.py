"""Create audio_assets table.

Revision ID: 005
Revises: 004
Create Date: 2025-12-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audio_assets table."""
    op.create_table(
        'audio_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('transcript_id', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transcript_id'], ['transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audio_assets_project_id', 'audio_assets', ['project_id'], unique=False)
    op.create_index('ix_audio_assets_transcript_id', 'audio_assets', ['transcript_id'], unique=False)
    op.create_index('ix_audio_assets_sha256', 'audio_assets', ['sha256'], unique=True)
    op.create_index('ix_audio_assets_created_at', 'audio_assets', ['created_at'], unique=False)
    op.create_index('idx_audio_transcript', 'audio_assets', ['transcript_id'], unique=False)
    op.create_index('idx_audio_project', 'audio_assets', ['project_id'], unique=False)


def downgrade() -> None:
    """Drop audio_assets table."""
    op.drop_index('idx_audio_project', table_name='audio_assets')
    op.drop_index('idx_audio_transcript', table_name='audio_assets')
    op.drop_index('ix_audio_assets_created_at', table_name='audio_assets')
    op.drop_index('ix_audio_assets_sha256', table_name='audio_assets')
    op.drop_index('ix_audio_assets_transcript_id', table_name='audio_assets')
    op.drop_index('ix_audio_assets_project_id', table_name='audio_assets')
    op.drop_table('audio_assets')

