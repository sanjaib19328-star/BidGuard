"""compliance_matrix_and_findings

Revision ID: 009_compliance_matrix_and_findings
Revises: 008_verification_center
Create Date: 2026-09-22 15:30:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '009_compliance_matrix_and_findings'
down_revision: Union[str, None] = '008_verification_center'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

matrix_item_status_enum = postgresql.ENUM(
    'COMPLIANT',
    'NON_COMPLIANT',
    'PARTIAL',
    'NOT_VERIFIABLE',
    'EXEMPT_MSE',
    name='matrix_item_status_enum',
    create_type=False,
)

finding_severity_enum = postgresql.ENUM(
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW',
    name='finding_severity_enum',
    create_type=False,
)

finding_type_enum = postgresql.ENUM(
    'MISSING_DOCUMENT',
    'VALUE_SHORTFALL',
    'IDENTITY_MISMATCH',
    'EXPIRED_CERTIFICATE',
    'COMMERCIAL_DEVIATION',
    'TECHNICAL_SHORTFALL',
    'UNAUTHORIZED_DECLARATION',
    name='finding_type_enum',
    create_type=False,
)

finding_review_status_enum = postgresql.ENUM(
    'PENDING',
    'ACCEPTED',
    'REJECTED',
    'OVERRIDDEN',
    'CLARIFICATION_REQUESTED',
    name='finding_review_status_enum',
    create_type=False,
)


def upgrade() -> None:
    # 1. Create Enums
    matrix_item_status_enum.create(op.get_bind(), checkfirst=True)
    finding_severity_enum.create(op.get_bind(), checkfirst=True)
    finding_type_enum.create(op.get_bind(), checkfirst=True)
    finding_review_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create evaluation_matrix_items table
    op.create_table(
        'evaluation_matrix_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bidder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bidders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('compliance_rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('compliance_rules.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tender_requirements.id', ondelete='SET NULL'), nullable=True),
        sa.Column('dimension', sa.String(50), nullable=True),
        sa.Column('status', matrix_item_status_enum, server_default='NOT_VERIFIABLE', nullable=False),
        sa.Column('required_value', sa.Text(), nullable=True),
        sa.Column('bidder_extracted_value', sa.Text(), nullable=True),
        sa.Column('deviation_magnitude', sa.Float(), nullable=True),
        sa.Column('is_statutory', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('confidence_score', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_matrix_tender_bidder', 'evaluation_matrix_items', ['tender_id', 'bidder_id'])
    op.create_index('ix_matrix_status', 'evaluation_matrix_items', ['status'])
    op.create_index('ix_matrix_rule', 'evaluation_matrix_items', ['compliance_rule_id'])
    op.create_index('ix_matrix_req', 'evaluation_matrix_items', ['requirement_id'])

    # 3. Create officer_findings table
    op.create_table(
        'officer_findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bidder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bidders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('matrix_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evaluation_matrix_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('severity', finding_severity_enum, server_default='MEDIUM', nullable=False),
        sa.Column('finding_type', finding_type_enum, nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('review_status', finding_review_status_enum, server_default='PENDING', nullable=False),
        sa.Column('officer_notes', sa.Text(), nullable=True),
        sa.Column('overridden_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('overridden_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_officer_findings_tender_bidder', 'officer_findings', ['tender_id', 'bidder_id'])
    op.create_index('ix_officer_findings_severity', 'officer_findings', ['severity'])
    op.create_index('ix_officer_findings_status', 'officer_findings', ['review_status'])


def downgrade() -> None:
    op.drop_table('officer_findings')
    op.drop_table('evaluation_matrix_items')

    finding_review_status_enum.drop(op.get_bind(), checkfirst=True)
    finding_type_enum.drop(op.get_bind(), checkfirst=True)
    finding_severity_enum.drop(op.get_bind(), checkfirst=True)
    matrix_item_status_enum.drop(op.get_bind(), checkfirst=True)
