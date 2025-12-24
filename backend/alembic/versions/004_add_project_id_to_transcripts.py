"""add project_id to transcripts

Revision ID: 004
Revises: 003
Create Date: 2025-12-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add project_id column to transcripts table
    op.add_column('transcripts', sa.Column('project_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_transcripts_project_id'), 'transcripts', ['project_id'], unique=False)
    op.create_foreign_key('fk_transcripts_project_id', 'transcripts', 'projects', ['project_id'], ['id'], ondelete='SET NULL')
    
    # Add raw_integrity_hash column to transcripts (for integrity verification)
    op.add_column('transcripts', sa.Column('raw_integrity_hash', sa.String(), nullable=True))
    op.create_index(op.f('ix_transcripts_raw_integrity_hash'), 'transcripts', ['raw_integrity_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_transcripts_raw_integrity_hash'), table_name='transcripts')
    op.drop_column('transcripts', 'raw_integrity_hash')
    op.drop_constraint('fk_transcripts_project_id', 'transcripts', type_='foreignkey')
    op.drop_index(op.f('ix_transcripts_project_id'), table_name='transcripts')
    op.drop_column('transcripts', 'project_id')

