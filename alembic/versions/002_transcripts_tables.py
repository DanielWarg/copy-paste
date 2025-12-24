"""transcripts tables

Revision ID: 002
Revises: 001
Create Date: 2025-12-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Transcripts table
    op.create_table(
        'transcripts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('language', sa.String(), nullable=False, server_default='sv'),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='uploaded'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transcripts_title'), 'transcripts', ['title'], unique=False)
    op.create_index(op.f('ix_transcripts_source'), 'transcripts', ['source'], unique=False)
    op.create_index(op.f('ix_transcripts_language'), 'transcripts', ['language'], unique=False)
    op.create_index(op.f('ix_transcripts_status'), 'transcripts', ['status'], unique=False)
    op.create_index(op.f('ix_transcripts_created_at'), 'transcripts', ['created_at'], unique=False)

    # Transcript segments table
    op.create_table(
        'transcript_segments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transcript_id', sa.Integer(), nullable=False),
        sa.Column('start_ms', sa.Integer(), nullable=False),
        sa.Column('end_ms', sa.Integer(), nullable=False),
        sa.Column('speaker_label', sa.String(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['transcript_id'], ['transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transcript_segments_transcript_id'), 'transcript_segments', ['transcript_id'], unique=False)
    op.create_index(op.f('ix_transcript_segments_start_ms'), 'transcript_segments', ['start_ms'], unique=False)
    op.create_index(op.f('ix_transcript_segments_speaker_label'), 'transcript_segments', ['speaker_label'], unique=False)
    op.create_index('idx_segment_transcript_start', 'transcript_segments', ['transcript_id', 'start_ms'], unique=False)

    # Transcript audit events table
    op.create_table(
        'transcript_audit_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transcript_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('actor', sa.String(), nullable=True, server_default='system'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['transcript_id'], ['transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transcript_audit_events_transcript_id'), 'transcript_audit_events', ['transcript_id'], unique=False)
    op.create_index(op.f('ix_transcript_audit_events_action'), 'transcript_audit_events', ['action'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_transcript_audit_events_action'), table_name='transcript_audit_events')
    op.drop_index(op.f('ix_transcript_audit_events_transcript_id'), table_name='transcript_audit_events')
    op.drop_table('transcript_audit_events')
    op.drop_index('idx_segment_transcript_start', table_name='transcript_segments')
    op.drop_index(op.f('ix_transcript_segments_speaker_label'), table_name='transcript_segments')
    op.drop_index(op.f('ix_transcript_segments_start_ms'), table_name='transcript_segments')
    op.drop_index(op.f('ix_transcript_segments_transcript_id'), table_name='transcript_segments')
    op.drop_table('transcript_segments')
    op.drop_index(op.f('ix_transcripts_created_at'), table_name='transcripts')
    op.drop_index(op.f('ix_transcripts_status'), table_name='transcripts')
    op.drop_index(op.f('ix_transcripts_language'), table_name='transcripts')
    op.drop_index(op.f('ix_transcripts_source'), table_name='transcripts')
    op.drop_index(op.f('ix_transcripts_title'), table_name='transcripts')
    op.drop_table('transcripts')

