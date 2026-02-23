"""
Policy versioning service.
Handles metadata updates, version history snapshots, and restoration of past versions.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from app.models.policy import Policy, PolicyVersion, PolicyStatus
from app.schemas.policy import PolicyUpdateRequest
from app.core.exceptions import CivicLensException

logger = logging.getLogger(__name__)


class PolicyVersionError(CivicLensException):
    """Exception raised when policy versioning operations fail."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict] = None):
        super().__init__(message=message, status_code=status_code, details=details or {})


async def update_policy_metadata(
    policy_id: str, 
    update_data: PolicyUpdateRequest, 
    db: AsyncSession
) -> Policy:
    """
    Update policy metadata and snapshot the current state as a new version.
    
    The snapshot corresponds to the state BEFORE the update is applied.
    Example: 
    1. Current policy is v1.
    2. We call update_policy_metadata.
    3. A PolicyVersion record is created for v1 data.
    4. Policy is updated with new data and version becomes 2.
    """
    # Get policy
    stmt = select(Policy).where(Policy.policy_id == policy_id, Policy.deleted_at.is_(None))
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise PolicyVersionError(
             message=f"Policy with ID '{policy_id}' not found",
             status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Check if there are actual changes (excluding change_reason and changed_by)
    update_dict = update_data.model_dump(exclude_unset=True)
    change_reason = update_dict.pop("change_reason", None)
    changed_by = update_dict.pop("changed_by", "system")
    
    if not update_dict:
        logger.info(f"No metadata changes for policy {policy_id}, skipping version bump")
        return policy

    # Create snapshot of CURRENT version
    snapshot = PolicyVersion(
        policy_id=policy.id,
        version_number=policy.version,
        title=policy.title,
        description=policy.description,
        language=policy.language,
        jurisdiction=policy.jurisdiction,
        policy_type=policy.policy_type,
        effective_date=policy.effective_date,
        expiry_date=policy.expiry_date,
        source_url=policy.source_url,
        status=policy.status,
        changed_by=changed_by,
        change_reason=change_reason,
        created_at=datetime.utcnow()
    )
    db.add(snapshot)
    
    # Update policy metadata
    for key, value in update_dict.items():
        if hasattr(policy, key):
            setattr(policy, key, value)
    
    # Bump version and update timestamp
    policy.version += 1
    policy.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(policy)
    
    logger.info(f"Updated policy {policy_id} to version {policy.version}")
    return policy


async def list_policy_versions(
    policy_id: str, 
    db: AsyncSession
) -> List[PolicyVersion]:
    """Retrieve all historical snapshots for a policy."""
    # Get policy first to verify existence
    stmt = select(Policy).where(Policy.policy_id == policy_id, Policy.deleted_at.is_(None))
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise PolicyVersionError(
             message=f"Policy with ID '{policy_id}' not found",
             status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Get versions ordered by version_number desc
    v_stmt = select(PolicyVersion).where(
        PolicyVersion.policy_id == policy.id
    ).order_by(desc(PolicyVersion.version_number))
    
    v_result = await db.execute(v_stmt)
    return list(v_result.scalars().all())


async def get_policy_version(
    policy_id: str, 
    version_number: int, 
    db: AsyncSession
) -> PolicyVersion:
    """Retrieve a specific historical snapshot."""
    stmt = select(Policy).where(Policy.policy_id == policy_id, Policy.deleted_at.is_(None))
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise PolicyVersionError(
             message=f"Policy with ID '{policy_id}' not found",
             status_code=status.HTTP_404_NOT_FOUND
        )
    
    v_stmt = select(PolicyVersion).where(
        PolicyVersion.policy_id == policy.id,
        PolicyVersion.version_number == version_number
    )
    v_result = await db.execute(v_stmt)
    version = v_result.scalar_one_or_none()
    
    if not version:
        raise PolicyVersionError(
            message=f"Version '{version_number}' for policy '{policy_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
        
    return version


async def restore_policy_version(
    policy_id: str, 
    version_number: int, 
    db: AsyncSession
) -> Policy:
    """
    Restore a policy to its state at a previous version.
    This creates a snapshot of the current state before overwriting.
    """
    # Get current policy
    stmt = select(Policy).where(Policy.policy_id == policy_id, Policy.deleted_at.is_(None))
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise PolicyVersionError(
             message=f"Policy with ID '{policy_id}' not found",
             status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Get the version to restore from
    v_stmt = select(PolicyVersion).where(
        PolicyVersion.policy_id == policy.id,
        PolicyVersion.version_number == version_number
    )
    v_result = await db.execute(v_stmt)
    version_data = v_result.scalar_one_or_none()
    
    if not version_data:
        raise PolicyVersionError(
            message=f"Version '{version_number}' for policy '{policy_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Snapshot CURRENT state before restoring
    # This ensures we don't lose the state we're restoring AWAY from
    snapshot = PolicyVersion(
        policy_id=policy.id,
        version_number=policy.version,
        title=policy.title,
        description=policy.description,
        language=policy.language,
        jurisdiction=policy.jurisdiction,
        policy_type=policy.policy_type,
        effective_date=policy.effective_date,
        expiry_date=policy.expiry_date,
        source_url=policy.source_url,
        status=policy.status,
        changed_by="system",
        change_reason=f"Restored from version {version_number}",
        created_at=datetime.utcnow()
    )
    db.add(snapshot)
    
    # Restore fields
    policy.title = version_data.title
    policy.description = version_data.description
    policy.language = version_data.language
    policy.jurisdiction = version_data.jurisdiction
    policy.policy_type = version_data.policy_type
    policy.effective_date = version_data.effective_date
    policy.expiry_date = version_data.expiry_date
    policy.source_url = version_data.source_url
    policy.status = version_data.status
    
    # Bump version
    policy.version += 1
    policy.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(policy)
    
    logger.info(f"Restored policy {policy_id} to version {version_number} (new version is {policy.version})")
    return policy
