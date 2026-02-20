"""Add eligibility profile and check tables

Revision ID: 003_add_eligibility_tables
Revises: 002_add_embeddings
Create Date: 2026-02-20 17:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_add_eligibility_tables"
down_revision: Union[str, None] = "002_add_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # user_eligibility_profiles
    # ------------------------------------------------------------------
    op.create_table(
        "user_eligibility_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.String(50), unique=True, nullable=False),
        sa.Column("session_id", sa.String(100), nullable=False),
        # Financial
        sa.Column("annual_income", sa.Float(), nullable=True),
        sa.Column("household_size", sa.Integer(), nullable=True),
        sa.Column("filing_status", sa.String(30), nullable=True),
        # Demographics
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("citizenship_status", sa.String(30), nullable=True),
        sa.Column("is_veteran", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_disabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("has_dependents", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("num_dependents", sa.Integer(), nullable=True),
        # Employment
        sa.Column("employment_status", sa.String(30), nullable=True),
        sa.Column("employer_type", sa.String(30), nullable=True),
        sa.Column("years_employed", sa.Float(), nullable=True),
        # Education
        sa.Column("education_level", sa.String(30), nullable=True),
        sa.Column("is_student", sa.Boolean(), nullable=False, server_default="0"),
        # Location
        sa.Column("state", sa.String(2), nullable=True),
        sa.Column("location_type", sa.String(20), nullable=True),
        # Loans
        sa.Column("has_federal_student_loans", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("loan_in_default", sa.Boolean(), nullable=True),
        sa.Column("years_of_loan_payments", sa.Float(), nullable=True),
        sa.Column("received_pell_grant", sa.Boolean(), nullable=True),
        # Other
        sa.Column("has_health_insurance", sa.Boolean(), nullable=True),
        sa.Column("owns_home", sa.Boolean(), nullable=True),
        sa.Column("extra_attributes", sa.JSON(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_elig_profile_session", "user_eligibility_profiles", ["session_id"])
    op.create_index("idx_elig_profile_created", "user_eligibility_profiles", ["created_at"])

    # ------------------------------------------------------------------
    # eligibility_checks
    # ------------------------------------------------------------------
    op.create_table(
        "eligibility_checks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("check_id", sa.String(50), unique=True, nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("policy_id", sa.String(50), nullable=False),
        sa.Column("result", sa.String(20), nullable=False, server_default="needs_more_info"),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("criteria_matched", sa.JSON(), nullable=True),
        sa.Column("criteria_failed", sa.JSON(), nullable=True),
        sa.Column("missing_fields", sa.JSON(), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_elig_check_profile", "eligibility_checks", ["profile_id"])
    op.create_index("idx_elig_check_policy", "eligibility_checks", ["policy_id"])
    op.create_index("idx_elig_check_result", "eligibility_checks", ["result"])
    op.create_index("idx_elig_check_profile_policy", "eligibility_checks", ["profile_id", "policy_id"])


def downgrade() -> None:
    op.drop_table("eligibility_checks")
    op.drop_table("user_eligibility_profiles")
