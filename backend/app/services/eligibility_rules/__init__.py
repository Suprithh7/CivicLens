"""
eligibility_rules package
=========================
Public interface for the deterministic eligibility rule engine.

Usage::

    from app.services.eligibility_rules import run_eligibility_check, UnsupportedPolicyError

    result = run_eligibility_check(profile_orm_instance, "pslf")
    print(result.result)       # "eligible" | "not_eligible" | "partial" | "needs_more_info"
    print(result.explanation)  # plain-English summary
"""

from app.services.eligibility_rules.engine import (
    run_eligibility_check,
    supported_policy_slugs,
    UnsupportedPolicyError,
)
from app.services.eligibility_rules.pslf import RuleResult

__all__ = [
    "run_eligibility_check",
    "supported_policy_slugs",
    "UnsupportedPolicyError",
    "RuleResult",
]
