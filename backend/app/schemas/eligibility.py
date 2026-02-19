"""
Pydantic schemas for user eligibility profile and eligibility check endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


# ---------------------------------------------------------------------------
# Enum mirrors (Pydantic-compatible, matching ORM enums)
# ---------------------------------------------------------------------------

class FilingStatusEnum(str, Enum):
    SINGLE = "single"
    MARRIED_JOINT = "married_joint"
    MARRIED_SEPARATE = "married_separate"
    HEAD_OF_HOUSEHOLD = "head_of_household"


class CitizenshipStatusEnum(str, Enum):
    CITIZEN = "citizen"
    PERMANENT_RESIDENT = "permanent_resident"
    VISA_HOLDER = "visa_holder"
    UNDOCUMENTED = "undocumented"


class EmploymentStatusEnum(str, Enum):
    EMPLOYED_FULL_TIME = "employed_full_time"
    EMPLOYED_PART_TIME = "employed_part_time"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    RETIRED = "retired"
    STUDENT = "student"


class EmployerTypeEnum(str, Enum):
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    PRIVATE = "private"
    MILITARY = "military"
    EDUCATION = "education"


class EducationLevelEnum(str, Enum):
    LESS_THAN_HS = "less_than_hs"
    HIGH_SCHOOL = "high_school"
    SOME_COLLEGE = "some_college"
    ASSOCIATES = "associates"
    BACHELORS = "bachelors"
    GRADUATE = "graduate"


class LocationTypeEnum(str, Enum):
    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL = "rural"


class EligibilityResultEnum(str, Enum):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    PARTIAL = "partial"
    NEEDS_MORE_INFO = "needs_more_info"


# ---------------------------------------------------------------------------
# EligibilityProfile schemas
# ---------------------------------------------------------------------------

class EligibilityProfileCreate(BaseModel):
    """
    Input schema for creating or updating a user eligibility profile.

    All domain fields are optional — a user can supply as many or as few as
    they know.  The more fields provided, the more precise the eligibility
    determination will be.
    """
    session_id: str = Field(
        ...,
        max_length=100,
        description="Anonymous session identifier (e.g. UUID from localStorage)",
        examples=["sess_f3a9b12c-7d4e-4f1a-8b2e-0c5d6e7f8a9b"]
    )

    # Financial
    annual_income: Optional[float] = Field(
        None,
        ge=0,
        description="Annual household Adjusted Gross Income (AGI) in USD",
        examples=[75000.0]
    )
    household_size: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Total number of people in the household",
        examples=[3]
    )
    filing_status: Optional[FilingStatusEnum] = Field(
        None,
        description="Federal tax filing status"
    )

    # Demographics
    age: Optional[int] = Field(
        None,
        ge=0,
        le=130,
        description="Age of the primary applicant in years",
        examples=[34]
    )
    citizenship_status: Optional[CitizenshipStatusEnum] = Field(
        None,
        description="Immigration / citizenship status"
    )
    is_veteran: bool = Field(
        default=False,
        description="Whether the applicant is a military veteran"
    )
    is_disabled: bool = Field(
        default=False,
        description="Whether the applicant has a qualifying disability"
    )
    has_dependents: bool = Field(
        default=False,
        description="Whether the applicant claims any dependents"
    )
    num_dependents: Optional[int] = Field(
        None,
        ge=0,
        description="Number of dependents (only relevant when has_dependents=True)"
    )

    # Employment
    employment_status: Optional[EmploymentStatusEnum] = Field(
        None,
        description="Current employment situation"
    )
    employer_type: Optional[EmployerTypeEnum] = Field(
        None,
        description="Sector of the current employer"
    )
    years_employed: Optional[float] = Field(
        None,
        ge=0,
        description="Years of continuous employment with current employer",
        examples=[5.5]
    )

    # Education
    education_level: Optional[EducationLevelEnum] = Field(
        None,
        description="Highest completed level of formal education"
    )
    is_student: bool = Field(
        default=False,
        description="Whether the applicant is currently enrolled as a full-time student"
    )

    # Location
    state: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="Two-letter US state code (e.g. 'CA', 'TX')",
        examples=["CA"]
    )
    location_type: Optional[LocationTypeEnum] = Field(
        None,
        description="Urban / suburban / rural classification of the residence"
    )

    # Student loan specifics
    has_federal_student_loans: bool = Field(
        default=False,
        description="Whether the applicant holds federal student loans"
    )
    loan_in_default: Optional[bool] = Field(
        None,
        description="Whether any federal loans are currently in default"
    )
    years_of_loan_payments: Optional[float] = Field(
        None,
        ge=0,
        description="Number of years of qualifying loan payments made",
        examples=[10.0]
    )
    received_pell_grant: Optional[bool] = Field(
        None,
        description="Whether the applicant ever received a Pell Grant"
    )

    # Other common dimensions
    has_health_insurance: Optional[bool] = Field(
        None,
        description="Whether the applicant currently has health insurance coverage"
    )
    owns_home: Optional[bool] = Field(
        None,
        description="Whether the applicant owns their primary residence"
    )

    # Escape hatch for policy-specific fields
    extra_attributes: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description=(
            "Additional policy-specific eligibility attributes not covered "
            "by the standard fields (arbitrary key-value pairs)"
        ),
        examples=[{"monthly_rent": 1500, "first_time_homebuyer": True}]
    )

    @field_validator("state")
    @classmethod
    def state_must_be_uppercase(cls, v: Optional[str]) -> Optional[str]:
        """Ensure state codes are stored in uppercase (e.g. 'ca' → 'CA')."""
        return v.upper() if v else v

    @field_validator("num_dependents")
    @classmethod
    def dependents_count_requires_flag(
        cls, v: Optional[int], info: Any
    ) -> Optional[int]:
        """Warn if num_dependents is set but has_dependents is False."""
        # Soft validation: allow it but note inconsistency; service layer handles
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "sess_f3a9b12c-7d4e-4f1a-8b2e-0c5d6e7f8a9b",
                "annual_income": 72000.0,
                "household_size": 2,
                "filing_status": "single",
                "age": 29,
                "citizenship_status": "citizen",
                "employment_status": "employed_full_time",
                "employer_type": "government",
                "years_employed": 6.0,
                "education_level": "bachelors",
                "is_student": False,
                "state": "CA",
                "has_federal_student_loans": True,
                "loan_in_default": False,
                "years_of_loan_payments": 6.0,
                "received_pell_grant": True,
                "is_veteran": False,
                "is_disabled": False,
                "has_dependents": False
            }
        }
    )


class EligibilityProfilePublic(BaseModel):
    """Read-back schema for a persisted eligibility profile."""

    profile_id: str
    session_id: str

    # Financial
    annual_income: Optional[float] = None
    household_size: Optional[int] = None
    filing_status: Optional[FilingStatusEnum] = None

    # Demographics
    age: Optional[int] = None
    citizenship_status: Optional[CitizenshipStatusEnum] = None
    is_veteran: bool = False
    is_disabled: bool = False
    has_dependents: bool = False
    num_dependents: Optional[int] = None

    # Employment
    employment_status: Optional[EmploymentStatusEnum] = None
    employer_type: Optional[EmployerTypeEnum] = None
    years_employed: Optional[float] = None

    # Education
    education_level: Optional[EducationLevelEnum] = None
    is_student: bool = False

    # Location
    state: Optional[str] = None
    location_type: Optional[LocationTypeEnum] = None

    # Loans
    has_federal_student_loans: bool = False
    loan_in_default: Optional[bool] = None
    years_of_loan_payments: Optional[float] = None
    received_pell_grant: Optional[bool] = None

    # Other
    has_health_insurance: Optional[bool] = None
    owns_home: Optional[bool] = None
    extra_attributes: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# EligibilityCheck schemas
# ---------------------------------------------------------------------------

class EligibilityCheckRequest(BaseModel):
    """Request schema: check a stored profile against a specific policy."""

    profile_id: str = Field(
        ...,
        description="Unique identifier of the eligibility profile to evaluate",
        examples=["elig_abc123xyz"]
    )
    policy_id: str = Field(
        ...,
        description="Unique identifier of the policy to check against",
        examples=["pol_abc123xyz"]
    )
    model: Optional[str] = Field(
        None,
        description="Override the LLM model used for the check",
        examples=["gpt-4-turbo-preview"]
    )
    language: Optional[str] = Field(
        None,
        description="Language code for the explanation response (e.g. 'en', 'hi')",
        examples=["en"]
    )

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "profile_id": "elig_abc123xyz",
                "policy_id": "pol_abc123xyz"
            }
        }
    )


class EligibilityCheckResponse(BaseModel):
    """Response schema for a completed eligibility check."""

    check_id: str = Field(..., description="Unique identifier for this check record")
    profile_id: str = Field(..., description="Profile that was evaluated")
    policy_id: str = Field(..., description="Policy that was evaluated against")

    result: EligibilityResultEnum = Field(
        ...,
        description=(
            "Outcome: 'eligible', 'not_eligible', 'partial' (meets some criteria), "
            "or 'needs_more_info' (cannot determine)"
        )
    )
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="AI confidence in the determination (0 = none, 1 = certain)"
    )
    explanation: Optional[str] = Field(
        None,
        description="Plain-language explanation of why the result was reached"
    )

    criteria_matched: Optional[List[str]] = Field(
        None,
        description="Policy criteria that the profile satisfies"
    )
    criteria_failed: Optional[List[str]] = Field(
        None,
        description="Policy criteria that the profile does NOT satisfy"
    )
    missing_fields: Optional[List[str]] = Field(
        None,
        description="Profile fields needed to make a definitive determination"
    )

    model_used: Optional[str] = Field(
        None,
        description="LLM model that performed the evaluation"
    )
    created_at: datetime = Field(..., description="Timestamp of the check")

    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),  # allow 'model_used' field without warning
        json_schema_extra={
            "example": {
                "check_id": "chk_xyz789",
                "profile_id": "elig_abc123xyz",
                "policy_id": "pol_abc123xyz",
                "result": "eligible",
                "confidence_score": 0.91,
                "explanation": (
                    "You meet all key criteria: your income is below $125,000, "
                    "you have 6 years of qualifying payments, and you work "
                    "full-time for a government employer."
                ),
                "criteria_matched": [
                    "Annual income below $125,000",
                    "Federal student loans not in default",
                    "At least 10 years of qualifying payments",
                    "Full-time government employment"
                ],
                "criteria_failed": [],
                "missing_fields": [],
                "model_used": "gpt-4-turbo-preview",
                "created_at": "2026-02-19T16:10:00Z"
            }
        }
    )


class EligibilityCheckListResponse(BaseModel):
    """Paginated list of eligibility checks for a profile."""
    checks: List[EligibilityCheckResponse]
    total: int
    profile_id: str
