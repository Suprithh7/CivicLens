"""
Eligibility rule engine dispatcher.
Maps a policy_slug to its deterministic rule function and runs it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.eligibility_rules.pslf import check_pslf, RuleResult

if TYPE_CHECKING:
    from app.models.eligibility import UserEligibilityProfile


# ---------------------------------------------------------------------------
# Registry: policy_slug → rule function
# ---------------------------------------------------------------------------
# Add new policies here as they are implemented.

POLICY_RULES: dict[str, callable] = {
    "pslf": check_pslf,
}

# Human-readable display names for supported policy slugs
POLICY_DISPLAY_NAMES: dict[str, str] = {
    "pslf": "Public Service Loan Forgiveness (PSLF)",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class UnsupportedPolicyError(ValueError):
    """Raised when no deterministic rule exists for the given policy slug."""
    pass


def run_eligibility_check(
    profile: "UserEligibilityProfile",
    policy_slug: str,
) -> RuleResult:
    """
    Run the deterministic eligibility check for *policy_slug* against *profile*.

    Args:
        profile:     ORM instance of UserEligibilityProfile (or any object
                     with the same attributes — allows easy unit-testing with
                     plain dataclasses / SimpleNamespace).
        policy_slug: Lowercase identifier for the target policy, e.g. ``"pslf"``.

    Returns:
        RuleResult with result, confidence, matched/failed/missing criteria,
        and a plain-English explanation.

    Raises:
        UnsupportedPolicyError: If no deterministic rule exists for the slug.
    """
    slug = policy_slug.strip().lower()
    rule_fn = POLICY_RULES.get(slug)
    if rule_fn is None:
        supported = ", ".join(sorted(POLICY_RULES.keys()))
        raise UnsupportedPolicyError(
            f"No deterministic rule implemented for policy '{slug}'. "
            f"Supported slugs: {supported}"
        )
    return rule_fn(profile)


def supported_policy_slugs() -> list[str]:
    """Return the list of policy slugs with deterministic rules."""
    return sorted(POLICY_RULES.keys())
