"""
Eligibility endpoints — profile management and deterministic rule checks.
"""

from __future__ import annotations

import logging
import secrets
import string
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.eligibility import (
    EligibilityCheck,
    EligibilityResult,
    UserEligibilityProfile,
)
from app.schemas.eligibility import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    EligibilityProfileCreate,
    EligibilityProfilePublic,
    EligibilityResultEnum,
)
from app.services.eligibility_rules import (
    UnsupportedPolicyError,
    run_eligibility_check,
    supported_policy_slugs,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gen_id(prefix: str, length: int = 12) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return prefix + "".join(secrets.choice(alphabet) for _ in range(length))


def _profile_to_public(p: UserEligibilityProfile) -> EligibilityProfilePublic:
    return EligibilityProfilePublic.model_validate(p)


def _check_to_response(c: EligibilityCheck) -> EligibilityCheckResponse:
    return EligibilityCheckResponse.model_validate(c)


# ---------------------------------------------------------------------------
# Profile endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/profile",
    response_model=EligibilityProfilePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update eligibility profile",
    description=(
        "Submit personal details for eligibility matching. "
        "If a profile for this session_id already exists it is updated in-place. "
        "No personally identifiable information is required."
    ),
)
async def create_or_update_profile(
    body: EligibilityProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> EligibilityProfilePublic:
    """Create a new profile or overwrite the existing one for the session."""
    logger.info("Eligibility profile upsert: session=%s", body.session_id)

    # Check for existing profile with this session_id
    stmt = select(UserEligibilityProfile).where(
        UserEligibilityProfile.session_id == body.session_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    now = datetime.utcnow()
    data = body.model_dump(exclude={"session_id"})

    if existing:
        # Update in-place
        for field, value in data.items():
            setattr(existing, field, value)
        existing.updated_at = now
        await db.commit()
        await db.refresh(existing)
        logger.info("Profile updated: %s", existing.profile_id)
        return _profile_to_public(existing)

    # Create new profile
    profile = UserEligibilityProfile(
        profile_id=_gen_id("elig_"),
        session_id=body.session_id,
        created_at=now,
        updated_at=now,
        **data,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    logger.info("Profile created: %s", profile.profile_id)
    return _profile_to_public(profile)


@router.get(
    "/profile/{profile_id}",
    response_model=EligibilityProfilePublic,
    summary="Get eligibility profile",
)
async def get_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
) -> EligibilityProfilePublic:
    stmt = select(UserEligibilityProfile).where(
        UserEligibilityProfile.profile_id == profile_id
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found.")
    return _profile_to_public(profile)


# ---------------------------------------------------------------------------
# Check endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/check",
    response_model=EligibilityCheckResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run deterministic eligibility check",
    description=(
        "Evaluate a stored eligibility profile against a policy using "
        "deterministic rules (no LLM).  Currently supported policy slugs: "
        "`pslf` (Public Service Loan Forgiveness)."
    ),
)
async def run_check(
    body: EligibilityCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> EligibilityCheckResponse:
    """Run a deterministic policy eligibility check and persist the result."""
    logger.info(
        "Eligibility check: profile=%s policy=%s",
        body.profile_id, body.policy_id,
    )

    # Load profile
    stmt = select(UserEligibilityProfile).where(
        UserEligibilityProfile.profile_id == body.profile_id
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{body.profile_id}' not found.",
        )

    # Run deterministic rules
    try:
        rule_result = run_eligibility_check(profile, body.policy_id)
    except UnsupportedPolicyError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Map result string → ORM enum
    result_enum = EligibilityResult(rule_result.result)

    # Persist check record
    check = EligibilityCheck(
        check_id=_gen_id("chk_"),
        profile_id=profile.id,
        policy_id=body.policy_id,
        result=result_enum,
        confidence_score=rule_result.confidence,
        explanation=rule_result.explanation,
        criteria_matched=rule_result.matched,
        criteria_failed=rule_result.failed,
        missing_fields=rule_result.missing,
        model_used="deterministic_rules_v1",
        created_at=datetime.utcnow(),
    )
    db.add(check)
    await db.commit()
    await db.refresh(check)

    logger.info(
        "Check completed: %s → %s (confidence=%.2f)",
        check.check_id, rule_result.result, rule_result.confidence,
    )

    # Build response (profile_id must be the string ID, not the integer PK)
    return EligibilityCheckResponse(
        check_id=check.check_id,
        profile_id=body.profile_id,
        policy_id=check.policy_id,
        result=EligibilityResultEnum(rule_result.result),
        confidence_score=rule_result.confidence,
        explanation=rule_result.explanation,
        criteria_matched=rule_result.matched,
        criteria_failed=rule_result.failed,
        missing_fields=rule_result.missing,
        model_used=check.model_used,
        created_at=check.created_at,
    )


@router.get(
    "/check/{check_id}",
    response_model=EligibilityCheckResponse,
    summary="Get a saved eligibility check result",
)
async def get_check(
    check_id: str,
    db: AsyncSession = Depends(get_db),
) -> EligibilityCheckResponse:
    stmt = select(EligibilityCheck).where(EligibilityCheck.check_id == check_id)
    result = await db.execute(stmt)
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail=f"Check '{check_id}' not found.")

    # Resolve string profile_id from linked profile
    p_stmt = select(UserEligibilityProfile).where(
        UserEligibilityProfile.id == check.profile_id
    )
    p_result = await db.execute(p_stmt)
    profile = p_result.scalar_one_or_none()
    profile_id_str = profile.profile_id if profile else str(check.profile_id)

    return EligibilityCheckResponse(
        check_id=check.check_id,
        profile_id=profile_id_str,
        policy_id=check.policy_id,
        result=EligibilityResultEnum(check.result.value),
        confidence_score=check.confidence_score,
        explanation=check.explanation,
        criteria_matched=check.criteria_matched,
        criteria_failed=check.criteria_failed,
        missing_fields=check.missing_fields,
        model_used=check.model_used,
        created_at=check.created_at,
    )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

@router.get(
    "/supported-policies",
    summary="List policies with deterministic rules",
)
async def list_supported_policies():
    """Returns the list of policy slugs that have deterministic eligibility rules."""
    return {"policies": supported_policy_slugs()}
