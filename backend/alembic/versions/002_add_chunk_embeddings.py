"""Add embedding column to policy_chunks

Revision ID: 002_add_embeddings
Revises: 001_add_chunks
Create Date: 2026-02-10 22:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '002_add_embeddings'
down_revision: Union[str, None] = '001_add_chunks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add embedding column to policy_chunks table
    op.add_column('policy_chunks', sa.Column('embedding', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove embedding column from policy_chunks table
    op.drop_column('policy_chunks', 'embedding')
