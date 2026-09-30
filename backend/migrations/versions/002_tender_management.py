"""tender_management

Revision ID: 002_tender_management
Revises: 001_initial_phase1
Create Date: 2026-09-03 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_tender_management'
down_revision: Union[str, None] = '001_initial_phase1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns to tenders
    op.add_column('tenders', sa.Column('procuring_entity', sa.String(length=255), nullable=True))
    op.add_column('tenders', sa.Column('source_portal', sa.String(length=100), nullable=True))
    op.add_column('tenders', sa.Column('source_url', sa.String(length=500), nullable=True))
    op.add_column('tenders', sa.Column('issue_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tenders', sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))

    # 2. Add foreign key for created_by
    op.create_foreign_key(
        'fk_tenders_created_by_users',
        'tenders', 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index(op.f('ix_tenders_created_by'), 'tenders', ['created_by'], unique=False)

    # 3. Drop global unique index on tender_number
    op.drop_index('ix_tenders_tender_number', table_name='tenders')

    # 4. Create composite unique constraint on (organization_id, tender_number)
    op.create_unique_constraint(
        'uq_tenders_org_tender_number',
        'tenders',
        ['organization_id', 'tender_number']
    )

    # 5. Create non-unique index on tender_number for search speed
    op.create_index(op.f('ix_tenders_tender_number'), 'tenders', ['tender_number'], unique=False)
    op.create_index('ix_tenders_org_status', 'tenders', ['organization_id', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_tenders_org_status', table_name='tenders')
    op.drop_index(op.f('ix_tenders_tender_number'), table_name='tenders')
    op.drop_constraint('uq_tenders_org_tender_number', 'tenders', type_='unique')
    op.create_index('ix_tenders_tender_number', 'tenders', ['tender_number'], unique=True)
    
    op.drop_index(op.f('ix_tenders_created_by'), table_name='tenders')
    op.drop_constraint('fk_tenders_created_by_users', 'tenders', type_='foreignkey')

    op.drop_column('tenders', 'created_by')
    op.drop_column('tenders', 'issue_date')
    op.drop_column('tenders', 'source_url')
    op.drop_column('tenders', 'source_portal')
    op.drop_column('tenders', 'procuring_entity')
