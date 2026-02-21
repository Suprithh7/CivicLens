"""
SQLAlchemy models for user eligibility profiles and eligibility check results.

These models capture the user-provided inputs needed to evaluate whether a
citizen qualifies for a government program described in an uploaded policy.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    Float, Index, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FilingStatus(str, enum.Enum):
    """Tax filing status of the household."""
    SINGLE = "single"
    MARRIED_JOINT = "married_joint"
    MARRIED_SEPARATE = "married_separate"
    HEAD_OF_HOUSEHOLD = "head_of_household"


class CitizenshipStatus(str, enum.Enum):
    """Immigration / citizenship status of the applicant."""
    CITIZEN = "citizen"
    PERMANENT_RESIDENT = "permanent_resident"
    VISA_HOLDER = "visa_holder"
    UNDOCUMENTED = "undocumented"


class EmploymentStatus(str, enum.Enum):
    """Current employment situation of the applicant."""
    EMPLOYED_FULL_TIME = "employed_full_time"
    EMPLOYED_PART_TIME = "employed_part_time"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    RETIRED = "retired"
    STUDENT = "student"


class EmployerType(str, enum.Enum):
    """Sector of the applicant's employer — relevant for public-service programs."""
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    PRIVATE = "private"
    MILITARY = "military"
    EDUCATION = "education"


class EducationLevel(str, enum.Enum):
    """Highest completed level of education."""
    LESS_THAN_HS = "less_than_hs"
    HIGH_SCHOOL = "high_school"
    SOME_COLLEGE = "some_college"
    ASSOCIATES = "associates"
    BACHELORS = "bachelors"
    GRADUATE = "graduate"


class LocationType(str, enum.Enum):
    """Urban/rural classification of the applicant's residence."""
    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL = "rural"


class EligibilityResult(str, enum.Enum):
    """Outcome of an eligibility check."""
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    PARTIAL = "partial"           # Meets some but not all criteria
    NEEDS_MORE_INFO = "needs_more_info"  # Cannot determine without extra data


# ---------------------------------------------------------------------------
# UserEligibilityProfile
# ---------------------------------------------------------------------------

class UserEligibilityProfile(Base):
    """
    A reusable snapshot of a user's personal circumstances.

    Users fill this in once and can then check eligibility against multiple
    policies without re-entering their details each time.  Because CivicLens
    has no authentication yet, profiles are linked to an anonymous session.
    """
    __tablename__ = "user_eligibility_profiles"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Public-facing unique identifier (e.g. "elig_abc123xyz")
    profile_id = Column(String(50), unique=True, nullable=False, index=True)

    # Anonymous session identifier (e.g. browser-generated UUID stored in localStorage)
    session_id = Column(String(100), nullable=False, index=True)

    # -----------------------------------------------------------------------
    # Financial information
    # -----------------------------------------------------------------------
    annual_income = Column(Float, nullable=True)           # Household AGI in USD
    household_size = Column(Integer, nullable=True)        # Total people in household
    filing_status = Column(
        SQLEnum(FilingStatus), nullable=True
    )

    # -----------------------------------------------------------------------
    # Personal demographics
    # -----------------------------------------------------------------------
    age = Column(Integer, nullable=True)
    citizenship_status = Column(
        SQLEnum(CitizenshipStatus), nullable=True
    )
    is_veteran = Column(Boolean, nullable=False, default=False)
    is_disabled = Column(Boolean, nullable=False, default=False)
    has_dependents = Column(Boolean, nullable=False, default=False)
    num_dependents = Column(Integer, nullable=True)        # Null if has_dependents=False

    # -----------------------------------------------------------------------
    # Employment
    # -----------------------------------------------------------------------
    employment_status = Column(
        SQLEnum(EmploymentStatus), nullable=True
    )
    employer_type = Column(
        SQLEnum(EmployerType), nullable=True               # Null if unemployed / student
    )
    years_employed = Column(Float, nullable=True)          # Years at current employer

    # -----------------------------------------------------------------------
    # Education
    # -----------------------------------------------------------------------
    education_level = Column(
        SQLEnum(EducationLevel), nullable=True
    )
    is_student = Column(Boolean, nullable=False, default=False)  # Currently enrolled FT

    # -----------------------------------------------------------------------
    # Location
    # -----------------------------------------------------------------------
    state = Column(String(2), nullable=True)               # 2-letter US state code
    location_type = Column(
        SQLEnum(LocationType), nullable=True
    )

    # -----------------------------------------------------------------------
    # Student loan specifics  (particularly relevant for education policies)
    # -----------------------------------------------------------------------
    has_federal_student_loans = Column(Boolean, nullable=False, default=False)
    loan_in_default = Column(Boolean, nullable=True)       # Null if no federal loans
    years_of_loan_payments = Column(Float, nullable=True)  # Qualifying payment years
    received_pell_grant = Column(Boolean, nullable=True)

    # -----------------------------------------------------------------------
    # Other common eligibility dimensions
    # -----------------------------------------------------------------------
    has_health_insurance = Column(Boolean, nullable=True)
    owns_home = Column(Boolean, nullable=True)

    # -----------------------------------------------------------------------
    # Escape hatch: policy-specific attributes not covered above
    # -----------------------------------------------------------------------
    extra_attributes = Column(JSON, nullable=True, default=dict)

    # -----------------------------------------------------------------------
    # Timestamps
    # -----------------------------------------------------------------------
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False,
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # -----------------------------------------------------------------------
    # Relationships
    # -----------------------------------------------------------------------
    eligibility_checks = relationship(
        "EligibilityCheck",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="EligibilityCheck.created_at.desc()"
    )

    # -----------------------------------------------------------------------
    # Indexes
    # -----------------------------------------------------------------------
    __table_args__ = (
        Index("idx_elig_profile_session", "session_id"),
        Index("idx_elig_profile_created", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserEligibilityProfile("
            f"id={self.id}, profile_id={self.profile_id}, "
            f"session_id={self.session_id})>"
        )


# ---------------------------------------------------------------------------
# EligibilityCheck
# ---------------------------------------------------------------------------

class EligibilityCheck(Base):
    """
    Records the result of evaluating one eligibility profile against one policy.

    Each row is immutable once created — subsequent checks produce new rows so
    that the full history of evaluations is preserved.
    """
    __tablename__ = "eligibility_checks"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Public-facing unique identifier (e.g. "chk_xyz789")
    check_id = Column(String(50), unique=True, nullable=False, index=True)

    # Foreign key to the user profile
    profile_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    # Reference to the policy (external policy_id string from the policies table)
    policy_id = Column(String(50), nullable=False, index=True)

    # -----------------------------------------------------------------------
    # Check result
    # -----------------------------------------------------------------------
    result = Column(
        SQLEnum(EligibilityResult),
        nullable=False,
        default=EligibilityResult.NEEDS_MORE_INFO
    )
    confidence_score = Column(Float, nullable=True)        # 0.0 – 1.0

    # Plain-language explanation produced by the LLM
    explanation = Column(Text, nullable=True)

    # -----------------------------------------------------------------------
    # Structured breakdown of the decision
    # -----------------------------------------------------------------------
    # Criteria from the policy that the user's profile satisfies
    criteria_matched = Column(JSON, nullable=True)         # List[str]

    # Criteria from the policy that the user's profile does NOT satisfy
    criteria_failed = Column(JSON, nullable=True)          # List[str]

    # Fields the system would need to make a definitive determination
    missing_fields = Column(JSON, nullable=True)           # List[str]

    # -----------------------------------------------------------------------
    # Audit / provenance
    # -----------------------------------------------------------------------
    # Snapshot of the profile fields AS THEY WERE when this check ran;
    # ensures historical records are self-contained even if the profile changes
    profile_snapshot = Column(JSON, nullable=True)         # Dict[str, Any]

    # Identifies the rule set / engine version that produced this result
    engine_version = Column(String(50), nullable=True)     # e.g. "pslf_v1"

    # Raw policy slug as submitted by the caller (before normalisation)
    requested_policy_slug = Column(String(100), nullable=True)  # e.g. "PSLF"

    # -----------------------------------------------------------------------
    # Provenance
    # -----------------------------------------------------------------------
    model_used = Column(String(100), nullable=True)        # LLM that ran the check

    # -----------------------------------------------------------------------
    # Timestamp (immutable after creation)
    # -----------------------------------------------------------------------
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # -----------------------------------------------------------------------
    # Relationships
    # -----------------------------------------------------------------------
    profile = relationship(
        "UserEligibilityProfile",
        back_populates="eligibility_checks"
    )

    # -----------------------------------------------------------------------
    # Indexes
    # -----------------------------------------------------------------------
    __table_args__ = (
        Index("idx_elig_check_profile", "profile_id"),
        Index("idx_elig_check_policy", "policy_id"),
        Index("idx_elig_check_result", "result"),
        Index("idx_elig_check_profile_policy", "profile_id", "policy_id"),
        Index("idx_elig_check_created", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EligibilityCheck("
            f"id={self.id}, check_id={self.check_id}, "
            f"policy_id={self.policy_id}, result={self.result})>"
        )
