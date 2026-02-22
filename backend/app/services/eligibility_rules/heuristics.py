"""
Heuristic Inference Pre-Pass for the Eligibility Rule Engine
=============================================================

Applies one-directional, profile-wide inference rules to fill in ``None``
fields that can be **strongly implied** by adjacent profile data — *before*
the deterministic criterion checks run.

Design principles
-----------------
* **Non-destructive**: heuristics only fill in ``None`` values — they never
  overwrite an explicit ``True``, ``False``, or string value the user provided.
* **One-directional**: every implication is a ``A → B`` rule, never circular.
* **Transparent**: every rule that fires is recorded in
  ``InferredProfile.heuristics_applied`` so callers can tag inferred criteria
  in their output and surface them to the user.
* **Conservative**: rules are only applied when the implication is essentially
  definitional (e.g. a veteran is a citizen) or has very high probability (e.g.
  someone making qualifying loan payments is by definition not in default).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# InferredProfile
# ---------------------------------------------------------------------------

@dataclass
class InferredProfile:
    """
    A lightweight view over a ``UserEligibilityProfile`` (or any compatible
    object) with some ``None`` fields filled by heuristic rules.

    All PSLF-relevant attributes mirror the ORM column names so that the
    criterion checkers in ``pslf.py`` can accept either an ORM instance or
    an ``InferredProfile`` without modification.
    """
    # PSLF-relevant fields (mirrored from ORM)
    has_federal_student_loans: Optional[bool]
    loan_in_default: Optional[bool]
    employment_status: Optional[Any]   # str or EmploymentStatus enum
    employer_type: Optional[Any]       # str or EmployerType enum
    years_of_loan_payments: Optional[float]
    citizenship_status: Optional[Any]  # str or CitizenshipStatus enum

    # Pass-through demographic signals (used by the heuristics themselves)
    is_veteran: bool = False
    is_student: bool = False
    age: Optional[int] = None
    annual_income: Optional[float] = None

    # Audit trail: human-readable description of every rule that fired
    heuristics_applied: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Individual heuristic rules
# ---------------------------------------------------------------------------

def _get_val(field_val: Any) -> Optional[str]:
    """Normalise an enum or plain string to a comparable string (or None)."""
    if field_val is None:
        return None
    return field_val.value if hasattr(field_val, "value") else str(field_val)


def _rule_veteran_implies_citizen(p: InferredProfile) -> None:
    """
    U.S. military veterans are, by definition, U.S. citizens.
    If ``is_veteran=True`` and ``citizenship_status`` is unknown, infer citizen.
    """
    if p.is_veteran and p.citizenship_status is None:
        p.citizenship_status = "citizen"
        p.heuristics_applied.append(
            "Inferred citizenship_status='citizen' from is_veteran=True"
        )


def _rule_veteran_implies_government_employer(p: InferredProfile) -> None:
    """
    Active-duty veterans or those who list only veteran status with no employer
    type are employed by the military — a qualifying government entity for PSLF.
    Applied only when employer_type is unset.
    """
    if p.is_veteran and p.employer_type is None:
        p.employer_type = "government"
        p.heuristics_applied.append(
            "Inferred employer_type='government' from is_veteran=True"
        )


def _rule_employer_type_implies_full_time(p: InferredProfile) -> None:
    """
    If a *veteran* has had their employer_type inferred (or explicitly set to a
    qualifying public-service type) but left employment_status blank, it is
    safe to infer full-time employment.

    This rule is intentionally scoped to veterans only — for non-veterans,
    providing an employer_type while leaving employment_status blank is
    ambiguous (could be part-time, self-employed, etc.) and we do not infer.
    Applied only when:
    - is_veteran=True (so we know the employment context)
    - employment_status is None
    """
    if p.is_veteran and p.employer_type is not None and p.employment_status is None:
        p.employment_status = "employed_full_time"
        p.heuristics_applied.append(
            "Inferred employment_status='employed_full_time' from is_veteran=True with employer_type set"
        )


def _rule_payment_history_implies_not_in_default(p: InferredProfile) -> None:
    """
    Anyone who has made qualifying PSLF payments is, by definition, not in
    default — defaulted loans do not produce qualifying payments under the
    income-driven repayment plans that PSLF requires.

    Applied when:
    - has_federal_student_loans is True (or will have been inferred)
    - years_of_loan_payments >= 1.0  (at least one year of payments made)
    - loan_in_default is None

    We use >= 1.0 rather than the full 10.0 threshold to be conservative:
    even a single year of qualifying payments is incompatible with default.
    """
    loans_present = p.has_federal_student_loans is True
    has_payments = (
        p.years_of_loan_payments is not None
        and p.years_of_loan_payments >= 1.0
    )
    if loans_present and has_payments and p.loan_in_default is None:
        p.loan_in_default = False
        p.heuristics_applied.append(
            "Inferred loan_in_default=False from years_of_loan_payments >= 1.0 "
            "(qualifying payments cannot be made while in default)"
        )


# ---------------------------------------------------------------------------
# Ordered pipeline
# ---------------------------------------------------------------------------

_HEURISTIC_PIPELINE = [
    # Veteran rules first — they may set employer_type/citizenship which the
    # later rules can then refine further.
    _rule_veteran_implies_citizen,
    _rule_veteran_implies_government_employer,
    # Employer-presence → employment status (runs after veteran rule may have
    # set employer_type so the implication can fire for veterans too).
    _rule_employer_type_implies_full_time,
    # Payment history → not in default (independent of employment rules).
    _rule_payment_history_implies_not_in_default,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_heuristics(profile: Any) -> InferredProfile:
    """
    Build an :class:`InferredProfile` from *profile* and apply all heuristic
    inference rules in order.

    Parameters
    ----------
    profile:
        Any object with the PSLF-relevant attribute set (ORM instance,
        ``SimpleNamespace``, dataclass, etc.).  Attributes not present on the
        object are silently defaulted to ``None`` / ``False``.

    Returns
    -------
    InferredProfile
        A new object with heuristically-inferred fields filled in and an audit
        trail in ``heuristics_applied``.  The original *profile* is never
        mutated.
    """
    def _attr(name: str, default: Any = None) -> Any:
        return getattr(profile, name, default)

    inferred = InferredProfile(
        has_federal_student_loans=_attr("has_federal_student_loans"),
        loan_in_default=_attr("loan_in_default"),
        employment_status=_attr("employment_status"),
        employer_type=_attr("employer_type"),
        years_of_loan_payments=_attr("years_of_loan_payments"),
        citizenship_status=_attr("citizenship_status"),
        is_veteran=_attr("is_veteran", False) or False,
        is_student=_attr("is_student", False) or False,
        age=_attr("age"),
        annual_income=_attr("annual_income"),
    )

    for rule in _HEURISTIC_PIPELINE:
        rule(inferred)

    return inferred
