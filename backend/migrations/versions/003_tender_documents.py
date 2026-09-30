"""tender_documents

Revision ID: 003_tender_documents
Revises: 002_tender_management
Create Date: 2026-09-03 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_tender_documents'
down_revision: Union[str, None] = '002_tender_management'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rename uploaded_at to created_at if exists
    op.alter_column('tender_documents', 'uploaded_at', new_column_name='created_at')

    # 2. Add new columns to tender_documents
    op.add_column('tender_documents', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('tender_documents', sa.Column('original_filename', sa.String(length=255), nullable=True))
    op.add_column('tender_documents', sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('tender_documents', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))

    # Populate organization_id and original_filename if existing rows exist
    op.execute("""
        UPDATE tender_documents td
        SET organization_id = t.organization_id,
            original_filename = td.filename
        FROM tenders t
        WHERE td.tender_id = t.id;
    """)

    # Make organization_id and original_filename non-nullable
    op.alter_column('tender_documents', 'organization_id', nullable=False)
    op.alter_column('tender_documents', 'original_filename', nullable=False)

    # 3. Add foreign keys
    op.create_foreign_key(
        'fk_tender_documents_organization_id',
        'tender_documents', 'organizations',
        ['organization_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_tender_documents_uploaded_by_users',
        'tender_documents', 'users',
        ['uploaded_by'], ['id'],
        ondelete='SET NULL'
    )

    # 4. Add composite unique constraint on (tender_id, sha256_hash)
    op.create_unique_constraint(
        'uq_tender_documents_tender_sha256',
        'tender_documents',
        ['tender_id', 'sha256_hash']
    )

    # 5. Add indexes
    op.create_index(op.f('ix_tender_documents_organization_id'), 'tender_documents', ['organization_id'], unique=False)
    op.create_index(op.f('ix_tender_documents_uploaded_by'), 'tender_documents', ['uploaded_by'], unique=False)
    op.create_index(op.f('ix_tender_documents_processing_status'), 'tender_documents', ['processing_status'], unique=False)
    op.create_index(op.f('ix_tender_documents_sha256_hash'), 'tender_documents', ['sha256_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tender_documents_sha256_hash'), table_name='tender_documents')
    op.drop_index(op.f('ix_tender_documents_processing_status'), table_name='tender_documents')
    op.drop_index(op.f('ix_tender_documents_uploaded_by'), table_name='tender_documents')
    op.drop_index(op.f('ix_tender_documents_organization_id'), table_name='tender_documents')

    op.drop_constraint('uq_tender_documents_tender_sha256', 'tender_documents', type_='unique')
    op.drop_constraint('fk_tender_documents_uploaded_by_users', 'tender_documents', type_='foreignkey')
    op.drop_constraint('fk_tender_documents_organization_id', 'tender_documents', type_='foreignkey')

    op.drop_column('tender_documents', 'updated_at')
    op.drop_column('tender_documents', 'uploaded_by')
    op.drop_column('tender_documents', 'original_filename')
    op.drop_column('tender_documents', 'organization_id')

    op.alter_column('tender_documents', 'created_at', new_column_name='uploaded_at')
