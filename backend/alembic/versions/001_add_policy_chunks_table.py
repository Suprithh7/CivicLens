"""Add policy_chunks table

Revision ID: 001_add_chunks
Revises: 
Create Date: 2026-02-09 22:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '001_add_chunks'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create policy_chunks table
    op.create_table(
        'policy_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('chunk_size', sa.Integer(), nullable=False),
        sa.Column('start_char', sa.Integer(), nullable=False),
        sa.Column('end_char', sa.Integer(), nullable=False),
        sa.Column('page_numbers', sa.JSON(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_chunk_policy_index', 'policy_chunks', ['policy_id', 'chunk_index'])
    op.create_index('idx_chunk_policy', 'policy_chunks', ['policy_id'])
    op.create_index(op.f('ix_policy_chunks_id'), 'policy_chunks', ['id'])
    
    # Add CHUNKING to ProcessingStage enum (SQLite doesn't support ALTER TYPE, so we handle this in the model)
    # For SQLite, enum values are stored as strings, so no migration needed for enum changes


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_policy_chunks_id'), table_name='policy_chunks')
    op.drop_index('idx_chunk_policy', table_name='policy_chunks')
    op.drop_index('idx_chunk_policy_index', table_name='policy_chunks')
    
    # Drop table
    op.drop_table('policy_chunks')
