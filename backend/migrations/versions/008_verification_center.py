"""verification_center

Revision ID: 008_verification_center
Revises: 007_bidder_intelligence
Create Date: 2026-09-22 14:00:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '008_verification_center'
down_revision: Union[str, None] = '007_bidder_intelligence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

data_source_type_enum = postgresql.ENUM(
    'GSTN_PORTAL',
    'UDYAM_MSME',
    'CBDT_PAN',
    'API_SETU',
    'OPEN_DATA_GOV',
    name='data_source_type_enum',
    create_type=False,
)

connector_status_enum = postgresql.ENUM(
    'CONNECTED',
    'AUTH_REQUIRED',
    'SANDBOX_ACTIVE',
    'DISCONNECTED',
    name='connector_status_enum',
    create_type=False,
)

verification_result_status_enum = postgresql.ENUM(
    'VERIFIED',
    'MISMATCH',
    'NOT_FOUND',
    'INVALID_FORMAT',
    'INACTIVE_EXPIRED',
    'AUTH_REQUIRED',
    'ERROR',
    name='verification_result_status_enum',
    create_type=False,
)

name_match_verdict_enum = postgresql.ENUM(
    'EXACT_MATCH',
    'FORMATTING_VARIATION',
    'MINOR_VARIATION',
    'POTENTIAL_MISMATCH',
    'SERIOUS_MISMATCH',
    name='name_match_verdict_enum',
    create_type=False,
)


def upgrade() -> None:
    # 1. Create Enums
    data_source_type_enum.create(op.get_bind(), checkfirst=True)
    connector_status_enum.create(op.get_bind(), checkfirst=True)
    verification_result_status_enum.create(op.get_bind(), checkfirst=True)
    name_match_verdict_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create data_source_connectors table
    op.create_table(
        'data_source_connectors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('source_type', data_source_type_enum, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', connector_status_enum, server_default='SANDBOX_ACTIVE', nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('auth_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('last_health_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_data_source_connectors_org_type', 'data_source_connectors', ['organization_id', 'source_type'])
    op.create_index('ix_data_source_connectors_status', 'data_source_connectors', ['status'])

    # 3. Create verification_requests table
    op.create_table(
        'verification_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bidder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bidders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('connector_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('data_source_connectors.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verification_type', data_source_type_enum, nullable=False),
        sa.Column('identifier_value', sa.String(100), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_verification_requests_bidder', 'verification_requests', ['bidder_id'])
    op.create_index('ix_verification_requests_tender', 'verification_requests', ['tender_id'])
    op.create_index('ix_verification_requests_type', 'verification_requests', ['verification_type'])

    # 4. Create verification_results table
    op.create_table(
        'verification_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('verification_request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('verification_requests.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('bidder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bidders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_type', data_source_type_enum, nullable=False),
        sa.Column('status', verification_result_status_enum, nullable=False),
        sa.Column('sanitized_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('matched_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('name_match_score', sa.Float(), nullable=True),
        sa.Column('name_match_verdict', name_match_verdict_enum, nullable=True),
        sa.Column('discrepancies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('officer_action_required', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_verification_results_bidder', 'verification_results', ['bidder_id'])
    op.create_index('ix_verification_results_status', 'verification_results', ['status'])
    op.create_index('ix_verification_results_verdict', 'verification_results', ['name_match_verdict'])


def downgrade() -> None:
    op.drop_table('verification_results')
    op.drop_table('verification_requests')
    op.drop_table('data_source_connectors')

    name_match_verdict_enum.drop(op.get_bind(), checkfirst=True)
    verification_result_status_enum.drop(op.get_bind(), checkfirst=True)
    connector_status_enum.drop(op.get_bind(), checkfirst=True)
    data_source_type_enum.drop(op.get_bind(), checkfirst=True)
