"""tender_clauses

Revision ID: 004_tender_clauses
Revises: 003_tender_documents
Create Date: 2026-09-11 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_tender_clauses'
down_revision: Union[str, None] = '003_tender_documents'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

clause_category_enum = postgresql.ENUM(
    'ADMINISTRATIVE',
    'STATUTORY',
    'TECHNICAL',
    'COMMERCIAL',
    'FINANCIAL',
    'ELIGIBILITY',
    'SUBMISSION',
    'GENERAL',
    name='clause_category_enum',
    create_type=False,
)


def upgrade() -> None:
    # 1. Create enum type safely
    clause_category_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create tender_clauses table
    op.create_table(
        'tender_clauses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('clause_number', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('clause_text', sa.Text(), nullable=False),
        sa.Column('category', clause_category_enum, nullable=False),
        sa.Column('sequence_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('extraction_method', sa.String(length=50), server_default='RULE_BASED', nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE', name='fk_tender_clauses_tender_id'),
        sa.ForeignKeyConstraint(['document_id'], ['tender_documents.id'], ondelete='CASCADE', name='fk_tender_clauses_document_id'),
        sa.ForeignKeyConstraint(['page_id'], ['tender_pages.id'], ondelete='SET NULL', name='fk_tender_clauses_page_id'),
        sa.PrimaryKeyConstraint('id', name='pk_tender_clauses'),
    )

    # 3. Create indexes
    op.create_index(op.f('ix_tender_clauses_tender_id'), 'tender_clauses', ['tender_id'], unique=False)
    op.create_index(op.f('ix_tender_clauses_document_id'), 'tender_clauses', ['document_id'], unique=False)
    op.create_index(op.f('ix_tender_clauses_page_id'), 'tender_clauses', ['page_id'], unique=False)
    op.create_index(op.f('ix_tender_clauses_clause_number'), 'tender_clauses', ['clause_number'], unique=False)
    op.create_index(op.f('ix_tender_clauses_category'), 'tender_clauses', ['category'], unique=False)
    op.create_index('ix_tender_clauses_tender_category', 'tender_clauses', ['tender_id', 'category'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_tender_clauses_tender_category', table_name='tender_clauses')
    op.drop_index(op.f('ix_tender_clauses_category'), table_name='tender_clauses')
    op.drop_index(op.f('ix_tender_clauses_clause_number'), table_name='tender_clauses')
    op.drop_index(op.f('ix_tender_clauses_page_id'), table_name='tender_clauses')
    op.drop_index(op.f('ix_tender_clauses_document_id'), table_name='tender_clauses')
    op.drop_index(op.f('ix_tender_clauses_tender_id'), table_name='tender_clauses')

    op.drop_table('tender_clauses')

    clause_category_enum.drop(op.get_bind(), checkfirst=True)
