"""
Unit tests for the PSLF deterministic eligibility rule engine.
Tests cover all four result tiers and every individual criterion.
No database required — rules are exercised against plain Python objects.
"""

from __future__ import annotations

from types import SimpleNamespace
import pytest

from app.services.eligibility_rules.pslf import check_pslf, RuleResult
from app.services.eligibility_rules.engine import (
    run_eligibility_check,
    UnsupportedPolicyError,
    supported_policy_slugs,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _profile(**kwargs) -> SimpleNamespace:
    """
    Build a minimal profile-like object with sensible defaults.
    All PSLF fields default to the QUALIFYING value; individual tests
    override specific fields to exercise failure paths.
    """
    defaults = dict(
        has_federal_student_loans=True,
        loan_in_default=False,
        employment_status="employed_full_time",
        employer_type="government",
        years_of_loan_payments=10.0,
        citizenship_status="citizen",
        # fields NOT used by PSLF rules (present to mirror ORM shape)
        annual_income=None,
        household_size=None,
        age=None,
        is_veteran=False,
        is_disabled=False,
        has_dependents=False,
        num_dependents=None,
        is_student=False,
        education_level=None,
        state=None,
        location_type=None,
        filing_status=None,
        has_health_insurance=None,
        owns_home=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Fully eligible
# ---------------------------------------------------------------------------

class TestFullyEligible:
    def test_all_criteria_met(self):
        p = _profile()
        r = check_pslf(p)
        assert r.result == "eligible"
        assert r.confidence == 1.0
        assert len(r.failed) == 0
        assert len(r.missing) == 0
        assert len(r.matched) == 6

    def test_military_employer_eligible(self):
        r = check_pslf(_profile(employer_type="military"))
        assert r.result == "eligible"

    def test_nonprofit_employer_eligible(self):
        r = check_pslf(_profile(employer_type="nonprofit"))
        assert r.result == "eligible"

    def test_education_employer_eligible(self):
        r = check_pslf(_profile(employer_type="education"))
        assert r.result == "eligible"

    def test_permanent_resident_eligible(self):
        r = check_pslf(_profile(citizenship_status="permanent_resident"))
        assert r.result == "eligible"

    def test_exactly_10_years_payments(self):
        r = check_pslf(_profile(years_of_loan_payments=10.0))
        assert r.result == "eligible"

    def test_more_than_10_years_eligible(self):
        r = check_pslf(_profile(years_of_loan_payments=15.5))
        assert r.result == "eligible"


# ---------------------------------------------------------------------------
# Not eligible — hard failures
# ---------------------------------------------------------------------------

class TestNotEligible:
    def test_no_federal_loans(self):
        r = check_pslf(_profile(has_federal_student_loans=False))
        assert r.result == "not_eligible"
        assert any("federal" in f.lower() for f in r.failed)

    def test_loan_in_default(self):
        r = check_pslf(_profile(loan_in_default=True))
        assert r.result == "not_eligible"
        assert any("default" in f.lower() for f in r.failed)

    def test_not_full_time(self):
        r = check_pslf(_profile(employment_status="employed_part_time"))
        assert r.result == "not_eligible"
        assert any("full-time" in f.lower() for f in r.failed)

    def test_private_employer(self):
        r = check_pslf(_profile(employer_type="private"))
        assert r.result == "not_eligible"
        assert any("qualifying" in f.lower() for f in r.failed)

    def test_undocumented_not_eligible(self):
        r = check_pslf(_profile(citizenship_status="undocumented"))
        assert r.result == "not_eligible"
        assert any("citizen" in f.lower() for f in r.failed)

    def test_visa_holder_not_eligible(self):
        r = check_pslf(_profile(citizenship_status="visa_holder"))
        assert r.result == "not_eligible"

    def test_unemployed_not_eligible(self):
        r = check_pslf(_profile(employment_status="unemployed"))
        assert r.result == "not_eligible"

    def test_multiple_hard_failures(self):
        r = check_pslf(_profile(
            has_federal_student_loans=False,
            employment_status="unemployed",
        ))
        assert r.result == "not_eligible"
        assert len(r.failed) >= 2


# ---------------------------------------------------------------------------
# Partial — secondary criterion not met, core criteria pass
# ---------------------------------------------------------------------------

class TestPartial:
    def test_insufficient_payment_years(self):
        """Has loans + qualifying employment, but only 5 years of payments."""
        r = check_pslf(_profile(years_of_loan_payments=5.0))
        assert r.result == "partial"
        assert any("10 year" in f or "qualifying payment" in f.lower() for f in r.failed)

    def test_just_under_10_years(self):
        r = check_pslf(_profile(years_of_loan_payments=9.9))
        assert r.result == "partial"

    def test_zero_payment_years(self):
        r = check_pslf(_profile(years_of_loan_payments=0.0))
        assert r.result == "partial"


# ---------------------------------------------------------------------------
# Needs more info — missing required data
# ---------------------------------------------------------------------------

class TestNeedsMoreInfo:
    def test_missing_federal_loan_flag(self):
        r = check_pslf(_profile(has_federal_student_loans=None))
        assert r.result == "needs_more_info"
        assert len(r.missing) > 0

    def test_missing_employer_type(self):
        r = check_pslf(_profile(employer_type=None))
        assert r.result == "needs_more_info"

    def test_missing_employment_status(self):
        r = check_pslf(_profile(employment_status=None))
        assert r.result == "needs_more_info"

    def test_missing_citizenship(self):
        r = check_pslf(_profile(citizenship_status=None))
        assert r.result == "needs_more_info"

    def test_missing_payment_years(self):
        r = check_pslf(_profile(years_of_loan_payments=None))
        assert r.result == "needs_more_info"

    def test_loan_default_unknown_with_federal_loans(self):
        """has_federal_student_loans=True but loan_in_default=None → needs_more_info,
        and the missing list must call out the default criterion."""
        r = check_pslf(_profile(loan_in_default=None))
        assert r.result == "needs_more_info"
        assert any("default" in m.lower() for m in r.missing)

    def test_fully_blank_profile(self):
        """A profile with all PSLF fields unset → needs_more_info."""
        p = _profile(
            has_federal_student_loans=None,
            loan_in_default=None,
            employment_status=None,
            employer_type=None,
            years_of_loan_payments=None,
            citizenship_status=None,
        )
        r = check_pslf(p)
        assert r.result == "needs_more_info"
        assert len(r.missing) > 0
        assert len(r.matched) == 0


# ---------------------------------------------------------------------------
# Rule result fields
# ---------------------------------------------------------------------------

class TestResultFields:
    def test_explanation_is_non_empty(self):
        for call in [
            _profile(),
            _profile(has_federal_student_loans=False),
            _profile(years_of_loan_payments=5.0),
            _profile(employer_type=None),
        ]:
            r = check_pslf(call)
            assert isinstance(r.explanation, str) and len(r.explanation) > 20

    def test_confidence_eligible_is_one(self):
        """Fully eligible with all fields → confidence must be exactly 1.0."""
        r = check_pslf(_profile())
        assert r.confidence == 1.0

    def test_confidence_not_eligible_range(self):
        """not_eligible confidence falls in [0.85, 1.0]."""
        cases = [
            _profile(employment_status="employed_part_time"),  # all 6 answered
            _profile(employer_type="private"),
            _profile(citizenship_status="visa_holder"),
            _profile(loan_in_default=True),
            _profile(has_federal_student_loans=False),         # 5/6 answered
        ]
        for p in cases:
            r = check_pslf(p)
            assert r.result == "not_eligible"
            assert 0.85 <= r.confidence <= 1.0, f"conf={r.confidence} out of [0.85,1.0]"

    def test_confidence_partial_range(self):
        """partial confidence falls in [0.65, 1.0]."""
        for years in [5.0, 0.0]:
            r = check_pslf(_profile(years_of_loan_payments=years))
            assert r.result == "partial"
            assert 0.65 <= r.confidence <= 1.0, f"conf={r.confidence} out of [0.65,1.0]"

    def test_confidence_needs_more_info_range(self):
        """needs_more_info confidence falls in [0.0, 0.60]."""
        cases = [
            SimpleNamespace(has_federal_student_loans=None, loan_in_default=None,
                            employment_status=None, employer_type=None,
                            years_of_loan_payments=None, citizenship_status=None),
            _profile(employer_type=None),
            _profile(years_of_loan_payments=None),
        ]
        for p in cases:
            r = check_pslf(p)
            assert r.result == "needs_more_info"
            assert 0.0 <= r.confidence <= 0.60, f"conf={r.confidence} out of [0.0,0.60]"

    def test_confidence_fully_blank_is_zero(self):
        """Zero answered criteria → confidence must be 0.0."""
        blank = SimpleNamespace(
            has_federal_student_loans=None, loan_in_default=None,
            employment_status=None, employer_type=None,
            years_of_loan_payments=None, citizenship_status=None,
        )
        assert check_pslf(blank).confidence == 0.0

    def test_confidence_increases_with_completeness(self):
        """Providing more data raises confidence for needs_more_info."""
        few = _profile(employer_type=None, years_of_loan_payments=None, citizenship_status=None)
        more = _profile(years_of_loan_payments=None)
        assert check_pslf(few).result == check_pslf(more).result == "needs_more_info"
        assert check_pslf(more).confidence > check_pslf(few).confidence

    def test_confidence_not_eligible_all_answered_is_one(self):
        """When all 6 criteria are fully answered and one fails → confidence = 1.0."""
        r = check_pslf(_profile(employment_status="employed_part_time"))
        assert r.result == "not_eligible"
        assert r.confidence == 1.0

    def test_result_type_is_string(self):
        r = check_pslf(_profile())
        assert isinstance(r.result, str)
        assert r.result in {"eligible", "not_eligible", "partial", "needs_more_info"}


# ---------------------------------------------------------------------------
# Engine dispatcher
# ---------------------------------------------------------------------------

class TestEngine:
    def test_pslf_slug_dispatches_correctly(self):
        r = run_eligibility_check(_profile(), "pslf")
        assert r.result == "eligible"

    def test_case_insensitive_slug(self):
        r = run_eligibility_check(_profile(), "PSLF")
        assert r.result == "eligible"

    def test_unsupported_slug_raises(self):
        with pytest.raises(UnsupportedPolicyError):
            run_eligibility_check(_profile(), "medicaid")

    def test_supported_policy_slugs(self):
        slugs = supported_policy_slugs()
        assert "pslf" in slugs
        assert isinstance(slugs, list)
