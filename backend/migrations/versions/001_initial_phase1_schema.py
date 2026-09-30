"""initial_phase1_schema

Revision ID: 001_initial_phase1
Revises: 
Create Date: 2026-09-02 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_phase1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums
    user_role_enum = postgresql.ENUM(
        'ADMIN', 'PROCUREMENT_OFFICER', 'REVIEWER', 'AUDITOR',
        name='user_role_enum',
        create_type=False
    )
    user_role_enum.create(op.get_bind(), checkfirst=True)

    tender_status_enum = postgresql.ENUM(
        'DRAFT', 'PROCESSING', 'READY', 'UNDER_REVIEW', 'COMPLETED', 'ARCHIVED',
        name='tender_status_enum',
        create_type=False
    )
    tender_status_enum.create(op.get_bind(), checkfirst=True)

    document_processing_status_enum = postgresql.ENUM(
        'UPLOADED', 'PROCESSING', 'PROCESSED', 'FAILED',
        name='document_processing_status_enum',
        create_type=False
    )
    document_processing_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 3. Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)

    # 4. Create tenders table
    op.create_table(
        'tenders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tender_number', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tender_type', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('submission_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opening_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', tender_status_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenders_organization_id'), 'tenders', ['organization_id'], unique=False)
    op.create_index(op.f('ix_tenders_tender_number'), 'tenders', ['tender_number'], unique=True)

    # 5. Create tender_documents table
    op.create_table(
        'tender_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('processing_status', document_processing_status_enum, nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tender_documents_tender_id'), 'tender_documents', ['tender_id'], unique=False)

    # 6. Create tender_pages table
    op.create_table(
        'tender_pages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['tender_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tender_pages_document_id'), 'tender_pages', ['document_id'], unique=False)

    # 7. Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('previous_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_actor_user_id'), 'audit_logs', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_organization_id'), 'audit_logs', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_organization_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index(op.f('ix_tender_pages_document_id'), table_name='tender_pages')
    op.drop_table('tender_pages')

    op.drop_index(op.f('ix_tender_documents_tender_id'), table_name='tender_documents')
    op.drop_table('tender_documents')

    op.drop_index(op.f('ix_tenders_tender_number'), table_name='tenders')
    op.drop_index(op.f('ix_tenders_organization_id'), table_name='tenders')
    op.drop_table('tenders')

    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    op.drop_table('organizations')

    op.execute('DROP TYPE IF EXISTS document_processing_status_enum')
    op.execute('DROP TYPE IF EXISTS tender_status_enum')
    op.execute('DROP TYPE IF EXISTS user_role_enum')
