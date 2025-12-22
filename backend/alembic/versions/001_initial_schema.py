"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

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
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('url', sa.String(2048), nullable=False, unique=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500)),
        sa.Column('raw_content', sa.Text()),
        sa.Column('source_hash', sa.String(64), nullable=False),
        sa.Column('content_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('metadata', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_source_hash', 'sources', ['source_hash'])
    op.create_index('idx_source_url', 'sources', ['url'])
    
    # Create chunks table
    op.create_table(
        'chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('text_hash', sa.String(64), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('token_count', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id']),
    )
    op.create_index('idx_chunk_text_hash', 'chunks', ['text_hash'])
    op.create_index('idx_chunk_source', 'chunks', ['source_id', 'chunk_index'])
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('user_id', sa.String(100)),
        sa.Column('operation', sa.String(50), nullable=False),
        sa.Column('source_ids', postgresql.JSONB()),
        sa.Column('source_hash', sa.String(64)),
        sa.Column('model_name', sa.String(100)),
        sa.Column('prompt_version', sa.String(50)),
        sa.Column('retrieved_chunks', postgresql.JSONB()),
        sa.Column('output_hash', sa.String(64)),
        sa.Column('output_preview', sa.Text()),
        sa.Column('trace_id', sa.String(64)),
        sa.Column('metadata', postgresql.JSONB()),
    )
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_user', 'audit_logs', ['user_id', 'timestamp'])
    op.create_index('idx_audit_operation', 'audit_logs', ['operation', 'timestamp'])
    op.create_index('idx_audit_trace', 'audit_logs', ['trace_id'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('chunks')
    op.drop_table('sources')
    op.execute("DROP EXTENSION IF EXISTS vector")

