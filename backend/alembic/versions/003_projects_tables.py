"""projects tables

Revision ID: 003
Revises: 002
Create Date: 2025-12-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('sensitivity', sa.String(), nullable=False, server_default='standard'),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_working_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)
    op.create_index(op.f('ix_projects_sensitivity'), 'projects', ['sensitivity'], unique=False)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)
    op.create_index(op.f('ix_projects_created_at'), 'projects', ['created_at'], unique=False)
    op.create_index(op.f('ix_projects_started_working_at'), 'projects', ['started_working_at'], unique=False)

    # Project notes table
    op.create_table(
        'project_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('note_integrity_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_notes_project_id'), 'project_notes', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_notes_note_integrity_hash'), 'project_notes', ['note_integrity_hash'], unique=False)

    # Project files table
    op.create_table(
        'project_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('sha256', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('stored_encrypted', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sha256')
    )
    op.create_index(op.f('ix_project_files_project_id'), 'project_files', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_files_sha256'), 'project_files', ['sha256'], unique=False)

    # Project audit events table
    op.create_table(
        'project_audit_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False, server_default='info'),
        sa.Column('actor', sa.String(), nullable=True, server_default='system'),
        sa.Column('request_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_audit_events_project_id'), 'project_audit_events', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_audit_events_action'), 'project_audit_events', ['action'], unique=False)
    op.create_index(op.f('ix_project_audit_events_severity'), 'project_audit_events', ['severity'], unique=False)
    op.create_index(op.f('ix_project_audit_events_request_id'), 'project_audit_events', ['request_id'], unique=False)
    op.create_index('idx_audit_project_severity', 'project_audit_events', ['project_id', 'severity'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_audit_project_severity', table_name='project_audit_events')
    op.drop_index(op.f('ix_project_audit_events_request_id'), table_name='project_audit_events')
    op.drop_index(op.f('ix_project_audit_events_severity'), table_name='project_audit_events')
    op.drop_index(op.f('ix_project_audit_events_action'), table_name='project_audit_events')
    op.drop_index(op.f('ix_project_audit_events_project_id'), table_name='project_audit_events')
    op.drop_table('project_audit_events')
    op.drop_index(op.f('ix_project_files_sha256'), table_name='project_files')
    op.drop_index(op.f('ix_project_files_project_id'), table_name='project_files')
    op.drop_table('project_files')
    op.drop_index(op.f('ix_project_notes_note_integrity_hash'), table_name='project_notes')
    op.drop_index(op.f('ix_project_notes_project_id'), table_name='project_notes')
    op.drop_table('project_notes')
    op.drop_index(op.f('ix_projects_started_working_at'), table_name='projects')
    op.drop_index(op.f('ix_projects_created_at'), table_name='projects')
    op.drop_index(op.f('ix_projects_status'), table_name='projects')
    op.drop_index(op.f('ix_projects_sensitivity'), table_name='projects')
    op.drop_index(op.f('ix_projects_name'), table_name='projects')
    op.drop_table('projects')

