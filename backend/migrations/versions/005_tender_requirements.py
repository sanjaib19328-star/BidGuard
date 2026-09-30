"""tender_requirements

Revision ID: 005_tender_requirements
Revises: 004_tender_clauses
Create Date: 2026-09-11 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_tender_requirements'
down_revision: Union[str, None] = '004_tender_clauses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Reference existing clause_category_enum
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

# New enums
requirement_type_enum = postgresql.ENUM(
    'MIN_TURNOVER',
    'MIN_NET_WORTH',
    'MIN_EXPERIENCE',
    'MIN_SIMILAR_WORK_EXPERIENCE',
    'MIN_TECHNICAL_CAPACITY',
    'BID_VALIDITY',
    'DELIVERY_PERIOD',
    'WARRANTY_PERIOD',
    'EMD_REQUIRED',
    'PBG_REQUIRED',
    'PERFORMANCE_SECURITY',
    'GST_REGISTRATION',
    'PAN_REQUIRED',
    'STATUTORY_LICENSE',
    'LEGAL_REGISTRATION',
    'OEM_AUTHORIZATION',
    'AUTHORIZED_DEALER',
    'TECHNICAL_SPECIFICATION',
    'TECHNICAL_PARAMETER',
    'MODEL_REQUIREMENT',
    'BRAND_REQUIREMENT',
    'CERTIFICATION_REQUIRED',
    'ISO_CERTIFICATION',
    'QUALITY_CERTIFICATION',
    'DOCUMENT_REQUIRED',
    'DECLARATION_REQUIRED',
    'AFFIDAVIT_REQUIRED',
    'PRICE_REQUIREMENT',
    'PAYMENT_TERM',
    'TAX_REQUIREMENT',
    'ELIGIBILITY_CONDITION',
    'SUBMISSION_DEADLINE',
    'OTHER',
    name='requirement_type_enum',
    create_type=False,
)

requirement_applicability_enum = postgresql.ENUM(
    'ALL_BIDDERS',
    'OEM',
    'AUTHORIZED_DEALER',
    'MANUFACTURER',
    'MSME',
    'STARTUP',
    'DOMESTIC_BIDDER',
    'FOREIGN_BIDDER',
    'JOINT_VENTURE',
    'CONSORTIUM',
    'CONDITIONAL',
    'UNKNOWN',
    name='requirement_applicability_enum',
    create_type=False,
)

verification_method_enum = postgresql.ENUM(
    'DOCUMENT',
    'RULE',
    'CROSS_DOCUMENT',
    'EXTERNAL_REGISTRY',
    'MANUAL',
    name='verification_method_enum',
    create_type=False,
)

risk_hint_enum = postgresql.ENUM(
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL',
    name='risk_hint_enum',
    create_type=False,
)


def upgrade() -> None:
    # 1. Create enum types safely
    requirement_type_enum.create(op.get_bind(), checkfirst=True)
    requirement_applicability_enum.create(op.get_bind(), checkfirst=True)
    verification_method_enum.create(op.get_bind(), checkfirst=True)
    risk_hint_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create tender_requirements table
    op.create_table(
        'tender_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clause_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', clause_category_enum, nullable=False),
        sa.Column('requirement_type', requirement_type_enum, nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('operator', sa.String(length=20), nullable=True),
        sa.Column('value_numeric', sa.Float(), nullable=True),
        sa.Column('value_text', sa.String(length=500), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('period', sa.String(length=100), nullable=True),
        sa.Column('mandatory', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('applicability', requirement_applicability_enum, server_default='ALL_BIDDERS', nullable=False),
        sa.Column('applicability_condition', sa.Text(), nullable=True),
        sa.Column('required_evidence', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('verification_method', verification_method_enum, server_default='DOCUMENT', nullable=False),
        sa.Column('risk_hint', risk_hint_enum, server_default='MEDIUM', nullable=False),
        sa.Column('sequence_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('extraction_method', sa.String(length=50), server_default='RULE_BASED', nullable=False),
        sa.Column('confidence', sa.Float(), server_default='0.90', nullable=False),
        sa.Column('requirement_signature', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE', name='fk_tender_requirements_tender_id'),
        sa.ForeignKeyConstraint(['clause_id'], ['tender_clauses.id'], ondelete='CASCADE', name='fk_tender_requirements_clause_id'),
        sa.PrimaryKeyConstraint('id', name='pk_tender_requirements'),
    )

    # 3. Create indexes
    op.create_index(op.f('ix_tender_requirements_tender_id'), 'tender_requirements', ['tender_id'], unique=False)
    op.create_index(op.f('ix_tender_requirements_clause_id'), 'tender_requirements', ['clause_id'], unique=False)
    op.create_index(op.f('ix_tender_requirements_category'), 'tender_requirements', ['category'], unique=False)
    op.create_index(op.f('ix_tender_requirements_requirement_type'), 'tender_requirements', ['requirement_type'], unique=False)
    op.create_index(op.f('ix_tender_requirements_mandatory'), 'tender_requirements', ['mandatory'], unique=False)
    op.create_index(op.f('ix_tender_requirements_applicability'), 'tender_requirements', ['applicability'], unique=False)
    op.create_index(op.f('ix_tender_requirements_verification_method'), 'tender_requirements', ['verification_method'], unique=False)
    op.create_index(op.f('ix_tender_requirements_risk_hint'), 'tender_requirements', ['risk_hint'], unique=False)
    op.create_index(op.f('ix_tender_requirements_sequence_order'), 'tender_requirements', ['sequence_order'], unique=False)
    op.create_index(op.f('ix_tender_requirements_requirement_signature'), 'tender_requirements', ['requirement_signature'], unique=False)
    op.create_index('ix_tender_requirements_tender_category', 'tender_requirements', ['tender_id', 'category'], unique=False)
    op.create_index('ix_tender_requirements_tender_type', 'tender_requirements', ['tender_id', 'requirement_type'], unique=False)
    op.create_index('ix_tender_requirements_tender_signature', 'tender_requirements', ['tender_id', 'requirement_signature'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_tender_requirements_tender_signature', table_name='tender_requirements')
    op.drop_index('ix_tender_requirements_tender_type', table_name='tender_requirements')
    op.drop_index('ix_tender_requirements_tender_category', table_name='tender_requirements')
    op.drop_index(op.f('ix_tender_requirements_requirement_signature'), table_name='tender_requirements')
    op.drop_index(op.f('ix_tender_requirements_sequence_order'), table_name='tender_requirements')
    op.drop_index(op.f('ix_tender_requirements_risk_hint'), table_name='tender_requirements')
    op.drop_index(op.f('ix_tender_requirements_verification_method'), table_name='tender_requirements')
    op.drop_index(op.f('ix_tender_requirements_applicability'), table_name='tender_requirements')
    op.drop_index(op.f('ix_tender_requirements_mandatory'), table_name='tender_requirements')
    op.drop_index(op.f('ix_tender_requirements_requirement_type'), table_name='tender_requirements')
    op.drop_index(op.f('ix_tender_requirements_category'), table_name='tender_requirements')
    op.drop_index(op.f('ix_tender_requirements_clause_id'), table_name='tender_requirements')
    op.drop_index(op.f('ix_tender_requirements_tender_id'), table_name='tender_requirements')

    op.drop_table('tender_requirements')

    risk_hint_enum.drop(op.get_bind(), checkfirst=True)
    verification_method_enum.drop(op.get_bind(), checkfirst=True)
    requirement_applicability_enum.drop(op.get_bind(), checkfirst=True)
    requirement_type_enum.drop(op.get_bind(), checkfirst=True)
