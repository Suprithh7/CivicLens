"""Add policy_versions table

Revision ID: 004_add_policy_versions
Revises: 003_add_eligibility_tables
Create Date: 2026-02-23 22:20:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_add_policy_versions"
down_revision: Union[str, None] = "003_add_eligibility_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create policy_versions table
    op.create_table(
        'policy_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('jurisdiction', sa.String(length=100), nullable=True),
        sa.Column('policy_type', sa.String(length=50), nullable=True),
        sa.Column('effective_date', sa.DateTime(), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('changed_by', sa.String(length=255), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_policy_version_policy_id', 'policy_versions', ['policy_id'])
    op.create_index('idx_policy_version_number', 'policy_versions', ['policy_id', 'version_number'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_policy_version_number', table_name='policy_versions')
    op.drop_index('idx_policy_version_policy_id', table_name='policy_versions')
    
    # Drop table
    op.drop_table('policy_versions')
