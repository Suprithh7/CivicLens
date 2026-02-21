"""
Unit tests for eligibility check auditability.

Covers:
  - EligibilityCheckResponse serialises audit fields (profile_snapshot,
    engine_version, requested_policy_slug)
  - Audit fields can be None (backward-compat with old rows)
  - EligibilityCheckListResponse structure with populated checks
  - Session-level list response returns empty list for unknown session
  - Result filter enum validates correctly
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from app.models.eligibility import EligibilityResult
from app.schemas.eligibility import (
    EligibilityCheckListResponse,
    EligibilityCheckResponse,
    EligibilityResultEnum,
)

NOW = datetime.now(tz=timezone.utc)

SAMPLE_SNAPSHOT = {
    "annual_income": 72000.0,
    "household_size": 2,
    "filing_status": "single",
    "age": 29,
    "citizenship_status": "citizen",
    "is_veteran": False,
    "is_disabled": False,
    "has_dependents": False,
    "num_dependents": None,
    "employment_status": "employed_full_time",
    "employer_type": "government",
    "years_employed": 6.0,
    "education_level": "bachelors",
    "is_student": False,
    "state": "CA",
    "location_type": "urban",
    "has_federal_student_loans": True,
    "loan_in_default": False,
    "years_of_loan_payments": 10.0,
    "received_pell_grant": None,
    "has_health_insurance": None,
    "owns_home": None,
    "extra_attributes": {},
}


def _check_response(**overrides):
    base = dict(
        check_id="chk_abc123",
        profile_id="elig_xyz",
        policy_id="pslf",
        result="eligible",
        created_at=NOW,
    )
    base.update(overrides)
    return EligibilityCheckResponse(**base)


# ===========================================================================
# Audit fields on EligibilityCheckResponse
# ===========================================================================

class TestAuditFieldsOnResponse:

    def test_profile_snapshot_is_stored(self):
        """profile_snapshot round-trips through schema without loss."""
        resp = _check_response(profile_snapshot=SAMPLE_SNAPSHOT)
        assert resp.profile_snapshot is not None
        assert resp.profile_snapshot["annual_income"] == 72_000.0
        assert resp.profile_snapshot["citizenship_status"] == "citizen"
        assert resp.profile_snapshot["has_federal_student_loans"] is True

    def test_engine_version_stored(self):
        resp = _check_response(engine_version="pslf_v1")
        assert resp.engine_version == "pslf_v1"

    def test_requested_policy_slug_stored(self):
        resp = _check_response(requested_policy_slug="PSLF")
        assert resp.requested_policy_slug == "PSLF"

    def test_all_three_audit_fields_present(self):
        resp = _check_response(
            profile_snapshot=SAMPLE_SNAPSHOT,
            engine_version="pslf_v1",
            requested_policy_slug="pslf",
        )
        assert resp.profile_snapshot is not None
        assert resp.engine_version == "pslf_v1"
        assert resp.requested_policy_slug == "pslf"

    def test_audit_fields_are_optional(self):
        """Rows created before the audit columns existed must still deserialise."""
        resp = _check_response()  # no audit fields
        assert resp.profile_snapshot is None
        assert resp.engine_version is None
        assert resp.requested_policy_slug is None

    def test_profile_snapshot_preserves_nulls(self):
        """None values in the snapshot must be kept (not stripped)."""
        snapshot_with_nulls = {**SAMPLE_SNAPSHOT, "received_pell_grant": None}
        resp = _check_response(profile_snapshot=snapshot_with_nulls)
        assert resp.profile_snapshot["received_pell_grant"] is None

    def test_profile_snapshot_tri_state_false(self):
        """Explicit False values in the snapshot must be preserved."""
        snap = {**SAMPLE_SNAPSHOT, "loan_in_default": False}
        resp = _check_response(profile_snapshot=snap)
        assert resp.profile_snapshot["loan_in_default"] is False

    def test_profile_snapshot_stores_extra_attributes(self):
        snap = {**SAMPLE_SNAPSHOT, "extra_attributes": {"monthly_rent": 1500}}
        resp = _check_response(profile_snapshot=snap)
        assert resp.profile_snapshot["extra_attributes"]["monthly_rent"] == 1500


# ===========================================================================
# EligibilityCheckListResponse
# ===========================================================================

class TestCheckListResponse:

    def _make_list(self, n: int, **overrides):
        checks = [_check_response(check_id=f"chk_{i}", **overrides) for i in range(n)]
        return EligibilityCheckListResponse(
            checks=checks,
            total=n,
            profile_id="elig_xyz",
        )

    def test_list_response_total_matches_count(self):
        resp = self._make_list(5)
        assert resp.total == 5
        assert len(resp.checks) == 5

    def test_empty_list_is_valid(self):
        resp = EligibilityCheckListResponse(checks=[], total=0, profile_id="elig_xyz")
        assert resp.total == 0
        assert resp.checks == []

    def test_all_result_variants_in_list(self):
        """All four result types must be expressible in a list response."""
        results = list(EligibilityResultEnum)
        checks = [
            _check_response(check_id=f"chk_{i}", result=r)
            for i, r in enumerate(results)
        ]
        resp = EligibilityCheckListResponse(
            checks=checks, total=len(checks), profile_id="elig_xyz"
        )
        assert len(resp.checks) == 4

    def test_checks_contain_audit_fields_when_present(self):
        resp = self._make_list(
            3,
            profile_snapshot=SAMPLE_SNAPSHOT,
            engine_version="pslf_v1",
            requested_policy_slug="pslf",
        )
        for c in resp.checks:
            assert c.profile_snapshot is not None
            assert c.engine_version == "pslf_v1"
            assert c.requested_policy_slug == "pslf"

    def test_session_level_list_with_empty_profile_id(self):
        """Session-level lists have an empty string profile_id."""
        checks = [_check_response()]
        resp = EligibilityCheckListResponse(checks=checks, total=1, profile_id="")
        assert resp.profile_id == ""


# ===========================================================================
# Result filter enum validation
# ===========================================================================

class TestResultFilterEnum:

    @pytest.mark.parametrize("slug", [
        "eligible", "not_eligible", "partial", "needs_more_info"
    ])
    def test_all_result_slugs_are_valid_enum_values(self, slug):
        result_enum = EligibilityResult(slug)
        assert result_enum.value == slug

    def test_invalid_result_slug_raises_value_error(self):
        with pytest.raises(ValueError):
            EligibilityResult("maybe")


# ===========================================================================
# Profile snapshot content correctness
# ===========================================================================

class TestProfileSnapshotContent:

    def test_snapshot_has_all_expected_keys(self):
        expected_keys = {
            "annual_income", "household_size", "filing_status",
            "age", "citizenship_status", "is_veteran", "is_disabled",
            "has_dependents", "num_dependents",
            "employment_status", "employer_type", "years_employed",
            "education_level", "is_student",
            "state", "location_type",
            "has_federal_student_loans", "loan_in_default",
            "years_of_loan_payments", "received_pell_grant",
            "has_health_insurance", "owns_home",
            "extra_attributes",
        }
        resp = _check_response(profile_snapshot=SAMPLE_SNAPSHOT)
        assert expected_keys.issubset(resp.profile_snapshot.keys())

    def test_snapshot_key_count(self):
        resp = _check_response(profile_snapshot=SAMPLE_SNAPSHOT)
        assert len(resp.profile_snapshot) == 23  # all declared profile fields
