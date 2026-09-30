"""compliance_rules

Revision ID: 006_compliance_rules
Revises: 005_tender_requirements
Create Date: 2026-09-11 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006_compliance_rules'
down_revision: Union[str, None] = '005_tender_requirements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enums
compliance_rule_type_enum = postgresql.ENUM(
    'NUMERIC_THRESHOLD',
    'NUMERIC_RANGE',
    'REQUIRED_DOCUMENT',
    'BOOLEAN_REQUIREMENT',
    'TEXT_MATCH',
    'DATE_LIMIT',
    'EXISTENCE_CHECK',
    'CONDITIONAL_RULE',
    'UNSUPPORTED',
    name='compliance_rule_type_enum',
    create_type=False,
)

evaluation_status_enum = postgresql.ENUM(
    'PASS',
    'FAIL',
    'PARTIAL',
    'NOT_VERIFIABLE',
    'NOT_APPLICABLE',
    name='evaluation_status_enum',
    create_type=False,
)


def upgrade() -> None:
    # 1. Create enum types safely
    compliance_rule_type_enum.create(op.get_bind(), checkfirst=True)
    evaluation_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create compliance_rules table
    op.create_table(
        'compliance_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_type', compliance_rule_type_enum, nullable=False),
        sa.Column('rule_configuration', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('sequence_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['requirement_id'], ['tender_requirements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_compliance_rules_tender_id'), 'compliance_rules', ['tender_id'], unique=False)
    op.create_index(op.f('ix_compliance_rules_requirement_id'), 'compliance_rules', ['requirement_id'], unique=False)
    op.create_index(op.f('ix_compliance_rules_rule_type'), 'compliance_rules', ['rule_type'], unique=False)
    op.create_index(op.f('ix_compliance_rules_enabled'), 'compliance_rules', ['enabled'], unique=False)
    op.create_index(op.f('ix_compliance_rules_sequence_order'), 'compliance_rules', ['sequence_order'], unique=False)
    op.create_index('ix_compliance_rules_tender_type', 'compliance_rules', ['tender_id', 'rule_type'], unique=False)
    op.create_index('ix_compliance_rules_tender_seq', 'compliance_rules', ['tender_id', 'sequence_order'], unique=False)

    # 3. Create compliance_evaluations table
    op.create_table(
        'compliance_evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('evaluation_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bidder_id', sa.String(length=100), nullable=True),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', evaluation_status_enum, nullable=False),
        sa.Column('actual_value', sa.Text(), nullable=True),
        sa.Column('expected_value', sa.Text(), nullable=True),
        sa.Column('evidence_reference', sa.Text(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('evaluator_type', sa.String(length=50), server_default='DETERMINISTIC_ENGINE', nullable=False),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['requirement_id'], ['tender_requirements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rule_id'], ['compliance_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_compliance_evaluations_evaluation_run_id'), 'compliance_evaluations', ['evaluation_run_id'], unique=False)
    op.create_index(op.f('ix_compliance_evaluations_tender_id'), 'compliance_evaluations', ['tender_id'], unique=False)
    op.create_index(op.f('ix_compliance_evaluations_bidder_id'), 'compliance_evaluations', ['bidder_id'], unique=False)
    op.create_index(op.f('ix_compliance_evaluations_requirement_id'), 'compliance_evaluations', ['requirement_id'], unique=False)
    op.create_index(op.f('ix_compliance_evaluations_rule_id'), 'compliance_evaluations', ['rule_id'], unique=False)
    op.create_index(op.f('ix_compliance_evaluations_status'), 'compliance_evaluations', ['status'], unique=False)
    op.create_index('ix_compliance_evals_tender_run', 'compliance_evaluations', ['tender_id', 'evaluation_run_id'], unique=False)
    op.create_index('ix_compliance_evals_tender_status', 'compliance_evaluations', ['tender_id', 'status'], unique=False)
    op.create_index('ix_compliance_evals_bidder', 'compliance_evaluations', ['tender_id', 'bidder_id'], unique=False)


def downgrade() -> None:
    op.drop_table('compliance_evaluations')
    op.drop_table('compliance_rules')
    evaluation_status_enum.drop(op.get_bind(), checkfirst=True)
    compliance_rule_type_enum.drop(op.get_bind(), checkfirst=True)
