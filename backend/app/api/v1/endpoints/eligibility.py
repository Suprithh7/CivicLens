"""
Eligibility endpoints — profile management, deterministic rule checks, and audit log.
"""

from __future__ import annotations

import logging
import secrets
import string
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.eligibility import (
    EligibilityCheck,
    EligibilityResult,
    UserEligibilityProfile,
)
from app.schemas.eligibility import (
    EligibilityCheckListResponse,
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


def _profile_to_snapshot(p: UserEligibilityProfile) -> dict:
    """Return a plain-dict snapshot of the profile fields for audit storage."""
    fields = [
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
    ]
    snapshot: dict = {}
    for f in fields:
        val = getattr(p, f, None)
        # Enum → string for JSON serialisation
        if hasattr(val, "value"):
            val = val.value
        snapshot[f] = val
    return snapshot


def _check_to_response(
    check: EligibilityCheck,
    profile_id_str: str,
) -> EligibilityCheckResponse:
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
        profile_snapshot=check.profile_snapshot,
        engine_version=check.engine_version,
        requested_policy_slug=check.requested_policy_slug,
    )


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
# Check endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/check",
    response_model=EligibilityCheckResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run deterministic eligibility check",
    description=(
        "Evaluate a stored eligibility profile against a policy using "
        "deterministic rules (no LLM).  Currently supported policy slugs: "
        "`pslf` (Public Service Loan Forgiveness). "
        "Every check is persisted with a full point-in-time profile snapshot "
        "for auditability."
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

    # Capture profile snapshot BEFORE running the check
    snapshot = _profile_to_snapshot(profile)

    # Run deterministic rules
    try:
        rule_result = run_eligibility_check(profile, body.policy_id)
    except UnsupportedPolicyError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Map result string → ORM enum
    result_enum = EligibilityResult(rule_result.result)

    # Persist check record with full audit metadata
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
        # ── Audit fields ──────────────────────────────────────────────────
        profile_snapshot=snapshot,
        engine_version=f"{body.policy_id.lower().split('_')[0]}_v1",
        requested_policy_slug=body.policy_id,
    )
    db.add(check)
    await db.commit()
    await db.refresh(check)

    logger.info(
        "Check completed: %s → %s (confidence=%.2f)",
        check.check_id, rule_result.result, rule_result.confidence,
    )

    return _check_to_response(check, body.profile_id)


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

    return _check_to_response(check, profile_id_str)


@router.get(
    "/profile/{profile_id}/checks",
    response_model=EligibilityCheckListResponse,
    summary="List all eligibility checks for a profile",
    description=(
        "Returns the full audit history of eligibility checks run against a "
        "particular profile, newest first. Each record includes the "
        "`profile_snapshot` captured at check time."
    ),
)
async def list_checks_for_profile(
    profile_id: str,
    result_filter: Optional[str] = Query(
        None,
        alias="result",
        description="Filter by result: eligible | not_eligible | partial | needs_more_info",
    ),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> EligibilityCheckListResponse:
    """Return paginated check history for a profile."""
    # Resolve profile
    p_stmt = select(UserEligibilityProfile).where(
        UserEligibilityProfile.profile_id == profile_id
    )
    p_result = await db.execute(p_stmt)
    profile = p_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found.")

    # Build query
    base = select(EligibilityCheck).where(
        EligibilityCheck.profile_id == profile.id
    )
    if result_filter:
        try:
            result_enum = EligibilityResult(result_filter)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid result filter '{result_filter}'. "
                       f"Must be one of: eligible, not_eligible, partial, needs_more_info.",
            )
        base = base.where(EligibilityCheck.result == result_enum)

    # Count total (before pagination)
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # Fetch page, newest first
    page_stmt = (
        base
        .order_by(EligibilityCheck.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(page_stmt)).scalars().all()

    checks = [_check_to_response(c, profile_id) for c in rows]
    return EligibilityCheckListResponse(
        checks=checks,
        total=total,
        profile_id=profile_id,
    )


@router.get(
    "/checks",
    response_model=EligibilityCheckListResponse,
    summary="List eligibility checks for a session (audit log)",
    description=(
        "Returns the full cross-profile audit log for an anonymous session. "
        "Supports filtering by result and policy slug, and is paginated newest-first."
    ),
)
async def list_checks_for_session(
    session_id: str = Query(
        ...,
        description="Anonymous session identifier (e.g. from localStorage)",
    ),
    result_filter: Optional[str] = Query(
        None,
        alias="result",
        description="Filter by result: eligible | not_eligible | partial | needs_more_info",
    ),
    policy_id: Optional[str] = Query(
        None,
        description="Filter by policy ID or slug",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> EligibilityCheckListResponse:
    """Return all checks across all profiles belonging to a session."""
    # Fetch all profiles for the session
    p_stmt = select(UserEligibilityProfile).where(
        UserEligibilityProfile.session_id == session_id
    )
    p_rows = (await db.execute(p_stmt)).scalars().all()
    if not p_rows:
        # Return empty list rather than 404 — session may just be new
        return EligibilityCheckListResponse(checks=[], total=0, profile_id="")

    profile_pk_map = {p.id: p.profile_id for p in p_rows}

    # Build base query across all profiles for this session
    base = select(EligibilityCheck).where(
        EligibilityCheck.profile_id.in_(list(profile_pk_map.keys()))
    )
    if result_filter:
        try:
            result_enum = EligibilityResult(result_filter)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid result filter '{result_filter}'. "
                       f"Must be one of: eligible, not_eligible, partial, needs_more_info.",
            )
        base = base.where(EligibilityCheck.result == result_enum)
    if policy_id:
        base = base.where(EligibilityCheck.policy_id == policy_id)

    # Count total
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # Fetch page
    page_stmt = (
        base
        .order_by(EligibilityCheck.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(page_stmt)).scalars().all()

    checks = [
        _check_to_response(c, profile_pk_map.get(c.profile_id, str(c.profile_id)))
        for c in rows
    ]
    return EligibilityCheckListResponse(checks=checks, total=total, profile_id="")


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
