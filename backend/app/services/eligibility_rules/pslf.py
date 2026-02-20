"""
PSLF (Public Service Loan Forgiveness) Deterministic Eligibility Rule Engine
============================================================================

Evaluates a user's eligibility profile against the official PSLF criteria
using pure-Python conditional logic — no LLM, no external calls.

Official PSLF criteria (simplified):
1. Must hold qualifying federal student loans.
2. Loans must NOT be in default.
3. Must be employed full-time.
4. Employer must be a qualifying public-service entity
   (government, non-profit, military, or education).
5. Must have made at least 10 years (120 months) of qualifying payments.
6. Must be a U.S. citizen or lawful permanent resident.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.eligibility import UserEligibilityProfile


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class RuleResult:
    """
    Structured output from a deterministic eligibility rule evaluation.
    Mirrors the EligibilityCheck ORM fields so the caller can persist it
    directly.

    Confidence scoring (0.0 – 1.0) reflects both the result tier and the
    completeness of the profile data used to reach it:

    * ``eligible``         → 1.0  (all criteria confirmed)
    * ``not_eligible``     → 0.85 + 0.15 × completeness  (≥ 0.85)
    * ``partial``          → 0.65 + 0.35 × completeness  (≥ 0.65)
    * ``needs_more_info``  → completeness × 0.60          (0 – 0.60)

    where ``completeness = answered_criteria / total_criteria``.
    """
    result: str                              # eligible | not_eligible | partial | needs_more_info
    confidence: float = 1.0                  # 0.0 – 1.0, see docstring for formula
    matched: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    explanation: str = ""


# ---------------------------------------------------------------------------
# PSLF qualifying employer types
# ---------------------------------------------------------------------------

QUALIFYING_EMPLOYER_TYPES = {
    "government",
    "nonprofit",
    "military",
    "education",
}

QUALIFYING_CITIZENSHIP = {
    "citizen",
    "permanent_resident",
}

PSLF_QUALIFYING_PAYMENT_YEARS = 10.0  # 120 months

PSLF_FULL_TIME_STATUSES = {
    "employed_full_time",
}


# ---------------------------------------------------------------------------
# Criterion helpers  (each returns (passed: bool | None, label: str))
#   None  → required info is missing from the profile
# ---------------------------------------------------------------------------

def _check_has_federal_loans(p: "UserEligibilityProfile"):
    label = "Holds qualifying federal student loans"
    if p.has_federal_student_loans is None:
        return None, label
    return bool(p.has_federal_student_loans), label


def _check_not_in_default(p: "UserEligibilityProfile"):
    label = "Federal loans are NOT in default"
    if not p.has_federal_student_loans:
        # No loans → criterion vacuously inapplicable; treat as missing
        return None, label
    if p.loan_in_default is None:
        return None, label
    return not bool(p.loan_in_default), label


def _check_full_time_employment(p: "UserEligibilityProfile"):
    label = "Employed full-time"
    if p.employment_status is None:
        return None, label
    status_val = (
        p.employment_status.value
        if hasattr(p.employment_status, "value")
        else str(p.employment_status)
    )
    return status_val in PSLF_FULL_TIME_STATUSES, label


def _check_qualifying_employer(p: "UserEligibilityProfile"):
    label = "Employer is a qualifying public-service entity (government / non-profit / military / education)"
    if p.employer_type is None:
        return None, label
    emp_val = (
        p.employer_type.value
        if hasattr(p.employer_type, "value")
        else str(p.employer_type)
    )
    return emp_val in QUALIFYING_EMPLOYER_TYPES, label


def _check_qualifying_payments(p: "UserEligibilityProfile"):
    label = "Has made ≥ 10 years (120 months) of qualifying payments"
    if p.years_of_loan_payments is None:
        return None, label
    return p.years_of_loan_payments >= PSLF_QUALIFYING_PAYMENT_YEARS, label


def _check_citizenship(p: "UserEligibilityProfile"):
    label = "U.S. citizen or lawful permanent resident"
    if p.citizenship_status is None:
        return None, label
    cit_val = (
        p.citizenship_status.value
        if hasattr(p.citizenship_status, "value")
        else str(p.citizenship_status)
    )
    return cit_val in QUALIFYING_CITIZENSHIP, label


# Ordered list of all PSLF criterion checkers
PSLF_CRITERIA = [
    _check_has_federal_loans,
    _check_not_in_default,
    _check_full_time_employment,
    _check_qualifying_employer,
    _check_qualifying_payments,
    _check_citizenship,
]

TOTAL_PSLF_CRITERIA = len(PSLF_CRITERIA)


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

def _compute_confidence(
    result: str,
    matched: list[str],
    failed: list[str],
    missing: list[str],
) -> float:
    """
    Compute a 0.0 – 1.0 confidence score for a deterministic eligibility result.

    The score blends the *result tier* (how decisive the outcome is) with
    *data completeness* (what fraction of criteria had enough information to
    evaluate).

    Tiers:
    - eligible         → 1.0  (all criteria confirmed; maximum certainty)
    - not_eligible     → 0.85 + 0.15 × completeness
      Even a single confirmed hard failure makes us highly confident in the
      denial; more complete data moves score toward 1.0.
    - partial          → 0.65 + 0.35 × completeness
      Core requirements pass but secondary one(s) fail; more data = more sure.
    - needs_more_info  → completeness × 0.60
      Low ceiling (≤ 0.60) since we can't make a real call yet; having some
      data answered is better than none.
    """
    answered = len(matched) + len(failed)
    total = answered + len(missing)
    completeness = answered / total if total > 0 else 0.0

    if result == "eligible":
        return 1.0
    elif result == "not_eligible":
        raw = 0.85 + 0.15 * completeness
    elif result == "partial":
        raw = 0.65 + 0.35 * completeness
    else:  # needs_more_info
        raw = completeness * 0.60

    return round(raw, 4)


# ---------------------------------------------------------------------------
# Main rule-check function
# ---------------------------------------------------------------------------

def check_pslf(profile: "UserEligibilityProfile") -> RuleResult:
    """
    Run all PSLF criteria against *profile* and return a RuleResult.

    Decision logic:
    - If any **required** criterion is unknown (missing data): needs_more_info
      (unless other hard failures are already clear)
    - If ALL criteria pass: eligible
    - If any criterion definitively fails: not_eligible
      UNLESS only 1-2 optional criteria fail and the core loan/employment
      criteria pass → partial (applicant should explore more)
    """
    matched: list[str] = []
    failed: list[str] = []
    missing_fields: list[str] = []

    # Evaluate every criterion
    for checker in PSLF_CRITERIA:
        passed, label = checker(profile)
        if passed is None:
            missing_fields.append(label)
        elif passed:
            matched.append(label)
        else:
            failed.append(label)

    # ── Determine overall result ──────────────────────────────────────────

    if len(failed) == 0 and len(missing_fields) == 0:
        # Every criterion confirmed satisfied
        result = "eligible"
        explanation = (
            "You appear to qualify for Public Service Loan Forgiveness. "
            "Your profile meets all six key criteria: you hold federal student loans "
            "that are not in default, you are employed full-time by a qualifying "
            "public-service employer, you have made the required 10 years of "
            "qualifying payments, and you are a U.S. citizen or permanent resident. "
            "We recommend submitting the PSLF Employment Certification Form to confirm."
        )

    elif len(failed) == 0 and len(missing_fields) > 0:
        # No failures but some info is missing
        result = "needs_more_info"
        missing_names = "; ".join(missing_fields)
        explanation = (
            f"We cannot make a definitive determination yet. "
            f"Please provide the following missing information: {missing_names}."
        )

    elif len(failed) > 0 and len(missing_fields) == 0:
        # Some criteria definitively failed, nothing missing
        # 'partial' if only secondary criteria fail and core ones pass
        core_labels = {
            "Holds qualifying federal student loans",
            "Federal loans are NOT in default",
            "Employed full-time",
            "Employer is a qualifying public-service entity (government / non-profit / military / education)",
            "U.S. citizen or lawful permanent resident",
        }
        core_failures = [f for f in failed if f in core_labels]
        if len(core_failures) == 0 and len(failed) <= 2:
            result = "partial"
            explanation = (
                "Your profile meets the core PSLF requirements (federal loans, "
                "qualifying employment) but does not yet satisfy all criteria: "
                + "; ".join(failed)
                + ". You may become eligible once these remaining criteria are met."
            )
        else:
            result = "not_eligible"
            explanation = (
                "Based on your profile, you do not currently qualify for PSLF. "
                "The following criteria are not met: "
                + "; ".join(failed) + "."
            )

    else:
        # Mix of failures and missing info — report the failures prominently
        core_labels = {
            "Holds qualifying federal student loans",
            "Federal loans are NOT in default",
            "Employed full-time",
            "Employer is a qualifying public-service entity (government / non-profit / military / education)",
            "U.S. citizen or lawful permanent resident",
        }
        core_failures = [f for f in failed if f in core_labels]
        if core_failures:
            result = "not_eligible"
            explanation = (
                "Your profile has one or more disqualifying factors: "
                + "; ".join(failed)
                + ". Additional information is also needed: "
                + "; ".join(missing_fields) + "."
            )
        else:
            result = "needs_more_info"
            explanation = (
                "We need more information to make a determination. "
                "Please provide: " + "; ".join(missing_fields) + ". "
                + (
                    f"Note: {'; '.join(failed)} currently does not meet PSLF requirements."
                    if failed else ""
                )
            )

    confidence = _compute_confidence(result, matched, failed, missing_fields)

    return RuleResult(
        result=result,
        confidence=confidence,
        matched=matched,
        failed=failed,
        missing=missing_fields,
        explanation=explanation.strip(),
    )
