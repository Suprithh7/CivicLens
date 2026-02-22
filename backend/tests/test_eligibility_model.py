"""
Unit tests for the User Eligibility data model.

Tests cover:
  - Pydantic schema validation (EligibilityProfileCreate)
  - Enum acceptance and rejection
  - Default values
  - State code normalisation
  - EligibilityCheckResponse serialisation
  - EligibilityCheckListResponse structure
"""

import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from app.schemas.eligibility import (
    EligibilityProfileCreate,
    EligibilityProfilePublic,
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    EligibilityCheckListResponse,
    FilingStatusEnum,
    CitizenshipStatusEnum,
    EmploymentStatusEnum,
    EmployerTypeEnum,
    EducationLevelEnum,
    LocationTypeEnum,
    EligibilityResultEnum,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_PROFILE = {
    "session_id": "sess_abc123",
}

FULL_PROFILE = {
    "session_id": "sess_abc123",
    "annual_income": 72000.0,
    "household_size": 2,
    "filing_status": "single",
    "age": 29,
    "citizenship_status": "citizen",
    "is_veteran": False,
    "is_disabled": False,
    "has_dependents": True,
    "num_dependents": 1,
    "employment_status": "employed_full_time",
    "employer_type": "government",
    "years_employed": 6.0,
    "education_level": "bachelors",
    "is_student": False,
    "state": "CA",
    "location_type": "urban",
    "has_federal_student_loans": True,
    "loan_in_default": False,
    "years_of_loan_payments": 6.0,
    "received_pell_grant": True,
    "has_health_insurance": True,
    "owns_home": False,
    "extra_attributes": {"monthly_rent": 1500},
}

NOW = datetime.now(tz=timezone.utc)

SAMPLE_CHECK_RESPONSE = {
    "check_id": "chk_xyz789",
    "profile_id": "elig_abc123",
    "policy_id": "pol_abc123",
    "result": "eligible",
    "confidence_score": 0.91,
    "explanation": "You meet all criteria.",
    "criteria_matched": ["Income below $125,000", "Government employer"],
    "criteria_failed": [],
    "missing_fields": [],
    "model_used": "gpt-4-turbo-preview",
    "created_at": NOW,
}


# ===========================================================================
# EligibilityProfileCreate — valid inputs
# ===========================================================================

class TestEligibilityProfileCreateValid:

    def test_minimal_required_fields_only(self):
        """Only session_id is required; everything else should be optional."""
        profile = EligibilityProfileCreate(**MINIMAL_PROFILE)
        assert profile.session_id == "sess_abc123"
        assert profile.annual_income is None
        assert profile.age is None
        assert profile.is_veteran is False
        assert profile.is_disabled is False
        assert profile.has_dependents is False
        assert profile.has_federal_student_loans is False
        assert profile.is_student is False
        assert profile.extra_attributes == {}

    def test_full_profile_accepted(self):
        """All fields should be accepted without validation errors."""
        profile = EligibilityProfileCreate(**FULL_PROFILE)
        assert profile.annual_income == 72000.0
        assert profile.household_size == 2
        assert profile.filing_status == FilingStatusEnum.SINGLE
        assert profile.citizenship_status == CitizenshipStatusEnum.CITIZEN
        assert profile.employment_status == EmploymentStatusEnum.EMPLOYED_FULL_TIME
        assert profile.employer_type == EmployerTypeEnum.GOVERNMENT
        assert profile.education_level == EducationLevelEnum.BACHELORS
        assert profile.location_type == LocationTypeEnum.URBAN
        assert profile.result is None if hasattr(profile, "result") else True

    def test_state_normalised_to_uppercase(self):
        """Lowercase state codes must be uppercased automatically."""
        profile = EligibilityProfileCreate(session_id="s1", state="ca")
        assert profile.state == "CA"

    def test_state_none_accepted(self):
        profile = EligibilityProfileCreate(session_id="s1", state=None)
        assert profile.state is None

    def test_extra_attributes_dict_accepted(self):
        profile = EligibilityProfileCreate(
            session_id="s1",
            extra_attributes={"monthly_rent": 900, "first_time_homebuyer": True}
        )
        assert profile.extra_attributes["monthly_rent"] == 900
        assert profile.extra_attributes["first_time_homebuyer"] is True

    def test_extra_attributes_defaults_to_empty_dict(self):
        profile = EligibilityProfileCreate(session_id="s1")
        assert profile.extra_attributes == {}

    def test_income_zero_accepted(self):
        profile = EligibilityProfileCreate(session_id="s1", annual_income=0.0)
        assert profile.annual_income == 0.0


# ===========================================================================
# EligibilityProfileCreate — validation failures
# ===========================================================================

class TestEligibilityProfileCreateInvalid:

    def test_missing_session_id_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            EligibilityProfileCreate(annual_income=50000.0)
        assert "session_id" in str(exc_info.value)

    def test_negative_income_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", annual_income=-1.0)

    def test_negative_age_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", age=-1)

    def test_age_over_130_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", age=131)

    def test_household_size_zero_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", household_size=0)

    def test_household_size_over_50_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", household_size=51)

    def test_negative_dependents_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", num_dependents=-1)

    def test_invalid_filing_status_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", filing_status="invalid_status")

    def test_invalid_citizenship_status_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", citizenship_status="alien")

    def test_invalid_employment_status_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", employment_status="gig_worker")

    def test_invalid_employer_type_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", employer_type="startup")

    def test_invalid_education_level_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", education_level="phd")

    def test_invalid_location_type_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", location_type="island")

    def test_state_too_long_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", state="CAL")

    def test_negative_years_of_loan_payments_rejected(self):
        """years_of_loan_payments < 0 must be rejected by schema (ge=0)."""
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", years_of_loan_payments=-0.5)

    def test_negative_years_employed_rejected(self):
        """years_employed < 0 must be rejected by schema (ge=0)."""
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", years_employed=-1.0)

    def test_blank_session_id_rejected(self):
        """An empty string session_id must be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EligibilityProfileCreate(session_id="")
        assert "session_id" in str(exc_info.value)

    def test_whitespace_only_session_id_rejected(self):
        """A whitespace-only session_id must be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EligibilityProfileCreate(session_id="   ")
        assert "session_id" in str(exc_info.value)

    def test_years_employed_exceeds_max_rejected(self):
        """years_employed > 70 must be rejected by schema (le=70)."""
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", years_employed=71.0)

    def test_years_of_loan_payments_exceeds_max_rejected(self):
        """years_of_loan_payments > 50 must be rejected by schema (le=50)."""
        with pytest.raises(ValidationError):
            EligibilityProfileCreate(session_id="s1", years_of_loan_payments=51.0)

    def test_dependents_flag_true_count_zero_rejected(self):
        """has_dependents=True with num_dependents=0 must fail cross-field validation."""
        with pytest.raises(ValidationError) as exc_info:
            EligibilityProfileCreate(
                session_id="s1",
                has_dependents=True,
                num_dependents=0,
            )
        assert "num_dependents" in str(exc_info.value)


# ===========================================================================
# Enum coverage
# ===========================================================================

class TestEnumCoverage:

    def test_all_filing_statuses_accepted(self):
        for status in FilingStatusEnum:
            p = EligibilityProfileCreate(session_id="s", filing_status=status)
            assert p.filing_status == status

    def test_all_citizenship_statuses_accepted(self):
        for status in CitizenshipStatusEnum:
            p = EligibilityProfileCreate(session_id="s", citizenship_status=status)
            assert p.citizenship_status == status

    def test_all_employment_statuses_accepted(self):
        for status in EmploymentStatusEnum:
            p = EligibilityProfileCreate(session_id="s", employment_status=status)
            assert p.employment_status == status

    def test_all_employer_types_accepted(self):
        for et in EmployerTypeEnum:
            p = EligibilityProfileCreate(session_id="s", employer_type=et)
            assert p.employer_type == et

    def test_all_education_levels_accepted(self):
        for level in EducationLevelEnum:
            p = EligibilityProfileCreate(session_id="s", education_level=level)
            assert p.education_level == level

    def test_all_location_types_accepted(self):
        for lt in LocationTypeEnum:
            p = EligibilityProfileCreate(session_id="s", location_type=lt)
            assert p.location_type == lt

    def test_all_eligibility_results_accepted(self):
        for result in EligibilityResultEnum:
            r = EligibilityCheckResponse(**{**SAMPLE_CHECK_RESPONSE, "result": result})
            assert r.result == result


# ===========================================================================
# EligibilityCheckRequest
# ===========================================================================

class TestEligibilityCheckRequest:

    def test_valid_request(self):
        req = EligibilityCheckRequest(
            profile_id="elig_abc123",
            policy_id="pol_abc123"
        )
        assert req.profile_id == "elig_abc123"
        assert req.policy_id == "pol_abc123"
        assert req.model is None
        assert req.language is None

    def test_with_optional_fields(self):
        req = EligibilityCheckRequest(
            profile_id="elig_abc123",
            policy_id="pol_abc123",
            model="gpt-4-turbo-preview",
            language="hi"
        )
        assert req.model == "gpt-4-turbo-preview"
        assert req.language == "hi"

    def test_missing_profile_id_raises(self):
        with pytest.raises(ValidationError):
            EligibilityCheckRequest(policy_id="pol_abc123")

    def test_missing_policy_id_raises(self):
        with pytest.raises(ValidationError):
            EligibilityCheckRequest(profile_id="elig_abc123")


# ===========================================================================
# EligibilityCheckResponse
# ===========================================================================

class TestEligibilityCheckResponse:

    def test_full_response_serialises(self):
        resp = EligibilityCheckResponse(**SAMPLE_CHECK_RESPONSE)
        assert resp.check_id == "chk_xyz789"
        assert resp.result == EligibilityResultEnum.ELIGIBLE
        assert resp.confidence_score == pytest.approx(0.91)
        assert len(resp.criteria_matched) == 2
        assert resp.criteria_failed == []
        assert resp.missing_fields == []

    def test_null_optional_fields_accepted(self):
        resp = EligibilityCheckResponse(
            check_id="chk_001",
            profile_id="elig_001",
            policy_id="pol_001",
            result="needs_more_info",
            created_at=NOW,
        )
        assert resp.confidence_score is None
        assert resp.explanation is None
        assert resp.criteria_matched is None
        assert resp.missing_fields is None

    def test_confidence_score_bounds(self):
        """Confidence score must be 0.0 – 1.0."""
        with pytest.raises(ValidationError):
            EligibilityCheckResponse(**{**SAMPLE_CHECK_RESPONSE, "confidence_score": 1.5})

        with pytest.raises(ValidationError):
            EligibilityCheckResponse(**{**SAMPLE_CHECK_RESPONSE, "confidence_score": -0.1})

    def test_invalid_result_enum_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityCheckResponse(**{**SAMPLE_CHECK_RESPONSE, "result": "maybe"})


# ===========================================================================
# EligibilityCheckListResponse
# ===========================================================================

class TestEligibilityCheckListResponse:

    def test_list_response_structure(self):
        check = EligibilityCheckResponse(**SAMPLE_CHECK_RESPONSE)
        resp = EligibilityCheckListResponse(
            checks=[check],
            total=1,
            profile_id="elig_abc123"
        )
        assert resp.total == 1
        assert len(resp.checks) == 1
        assert resp.checks[0].check_id == "chk_xyz789"

    def test_empty_checks_list(self):
        resp = EligibilityCheckListResponse(
            checks=[],
            total=0,
            profile_id="elig_abc123"
        )
        assert resp.total == 0
        assert resp.checks == []
