"""bidder_intelligence

Revision ID: 007_bidder_intelligence
Revises: 006_compliance_rules
Create Date: 2026-09-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '007_bidder_intelligence'
down_revision: Union[str, None] = '006_compliance_rules'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enums
document_processing_status_enum = postgresql.ENUM(
    'UPLOADED',
    'PROCESSING',
    'PROCESSED',
    'FAILED',
    name='document_processing_status_enum',
    create_type=False,
)

bidder_document_type_enum = postgresql.ENUM(
    'GST_CERTIFICATE',
    'PAN_CARD',
    'UDYAM_CERTIFICATE',
    'ASME_CERTIFICATE',
    'GA_DRAWING',
    'DESIGN_CALCULATION',
    'WPS_PQR',
    'MTC_REPORT',
    'NDT_REPORT',
    'PWHT_REPORT',
    'HYDROTEST_REPORT',
    'INTEGRITY_PACT',
    'ZERO_DEVIATION_DECLARATION',
    'MAKE_IN_INDIA_DECLARATION',
    'LAND_BORDER_DECLARATION',
    'POWER_OF_ATTORNEY',
    'FINANCIAL_AUDIT_REPORT',
    'PRIOR_EXPERIENCE_PROOF',
    'OTHER',
    name='bidder_document_type_enum',
    create_type=False,
)

mse_category_enum = postgresql.ENUM(
    'MICRO',
    'SMALL',
    'MEDIUM',
    'NOT_APPLICABLE',
    name='mse_category_enum',
    create_type=False,
)

entity_type_enum = postgresql.ENUM(
    'GSTIN',
    'PAN',
    'UDYAM_NUMBER',
    'COMPANY_NAME',
    'TRADE_NAME',
    'DATE',
    'FINANCIAL_TURNOVER',
    'ASME_STAMP',
    'PRESSURE_VALUE',
    'THICKNESS_VALUE',
    'ADDRESS',
    name='entity_type_enum',
    create_type=False,
)

participation_status_enum = postgresql.ENUM(
    'DRAFT',
    'SUBMITTED',
    'UNDER_REVIEW',
    'EVALUATED',
    'QUALIFIED',
    'DISQUALIFIED',
    name='participation_status_enum',
    create_type=False,
)


def upgrade() -> None:
    # 1. Create Enums
    bidder_document_type_enum.create(op.get_bind(), checkfirst=True)
    mse_category_enum.create(op.get_bind(), checkfirst=True)
    entity_type_enum.create(op.get_bind(), checkfirst=True)
    participation_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create bidders table
    op.create_table(
        'bidders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('legal_name', sa.String(255), nullable=False),
        sa.Column('trade_name', sa.String(255), nullable=True),
        sa.Column('gstin', sa.String(15), nullable=True),
        sa.Column('pan', sa.String(10), nullable=True),
        sa.Column('udyam_registration_number', sa.String(50), nullable=True),
        sa.Column('registered_address', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('primary_contact_person', sa.String(255), nullable=True),
        sa.Column('is_mse', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('mse_category', mse_category_enum, server_default='NOT_APPLICABLE', nullable=False),
        sa.Column('asme_stamp_holder', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('asme_certificate_number', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_bidders_org_legal_name', 'bidders', ['organization_id', 'legal_name'])
    op.create_index('ix_bidders_gstin', 'bidders', ['gstin'])
    op.create_index('ix_bidders_pan', 'bidders', ['pan'])
    op.create_index('ix_bidders_udyam', 'bidders', ['udyam_registration_number'])

    # 3. Create bidder_tender_participations table
    op.create_table(
        'bidder_tender_participations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('bidder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bidders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', participation_status_enum, server_default='DRAFT', nullable=False),
        sa.Column('submission_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('risk_level', sa.String(50), nullable=True),
        sa.Column('officer_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_bidder_tender_part', 'bidder_tender_participations', ['bidder_id', 'tender_id'], unique=True)
    op.create_index('ix_bidder_part_status', 'bidder_tender_participations', ['tender_id', 'status'])

    # 4. Create bidder_documents table
    op.create_table(
        'bidder_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('bidder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bidders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('document_type', bidder_document_type_enum, server_default='OTHER', nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('storage_path', sa.String(512), nullable=False),
        sa.Column('mime_type', sa.String(100), server_default='application/pdf', nullable=False),
        sa.Column('file_size', sa.Integer(), server_default='0', nullable=False),
        sa.Column('sha256_hash', sa.String(64), nullable=False),
        sa.Column('processing_status', document_processing_status_enum, server_default='UPLOADED', nullable=False),
        sa.Column('page_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_bidder_docs_bidder', 'bidder_documents', ['bidder_id'])
    op.create_index('ix_bidder_docs_tender', 'bidder_documents', ['tender_id'])
    op.create_index('ix_bidder_docs_type', 'bidder_documents', ['bidder_id', 'document_type'])

    # 5. Create bidder_document_pages table
    op.create_table(
        'bidder_document_pages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bidder_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('text_content', sa.Text(), server_default='', nullable=False),
        sa.Column('has_tables', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('extracted_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_bidder_doc_pages_doc_page', 'bidder_document_pages', ['document_id', 'page_number'], unique=True)

    # 6. Create extracted_entities table
    op.create_table(
        'extracted_entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('bidder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bidders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bidder_documents.id', ondelete='CASCADE'), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('entity_type', entity_type_enum, nullable=False),
        sa.Column('raw_value', sa.Text(), nullable=False),
        sa.Column('normalized_value', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('context_snippet', sa.Text(), nullable=True),
        sa.Column('bounding_box', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_extracted_entities_bidder', 'extracted_entities', ['bidder_id'])
    op.create_index('ix_extracted_entities_doc', 'extracted_entities', ['document_id'])
    op.create_index('ix_extracted_entities_type', 'extracted_entities', ['bidder_id', 'entity_type'])


def downgrade() -> None:
    op.drop_table('extracted_entities')
    op.drop_table('bidder_document_pages')
    op.drop_table('bidder_documents')
    op.drop_table('bidder_tender_participations')
    op.drop_table('bidders')

    participation_status_enum.drop(op.get_bind(), checkfirst=True)
    entity_type_enum.drop(op.get_bind(), checkfirst=True)
    mse_category_enum.drop(op.get_bind(), checkfirst=True)
    bidder_document_type_enum.drop(op.get_bind(), checkfirst=True)
