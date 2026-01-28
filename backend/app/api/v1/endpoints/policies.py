"""
Policy endpoints for document upload and management.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.schemas.policy import (
    PolicyUploadResponse, 
    PolicyPublic, 
    PolicyListResponse,
    PolicyStatusEnum,
    PolicyTypeEnum
)
from app.models.policy import Policy, PolicyStatus
from app.core.dependencies import get_db
from datetime import datetime
import os
import uuid
import hashlib
from pathlib import Path
from typing import Optional

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = Path("uploads/policies")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_pdf(file: UploadFile) -> None:
    """Validate uploaded file is a PDF and within size limits."""
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only PDF files are allowed. Got: {file_ext}"
        )
    
    # Check content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type. Expected 'application/pdf', got '{file.content_type}'"
        )


def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


@router.post(
    "/upload",
    response_model=PolicyUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Policy Document",
    description="Upload a policy document (PDF only). Maximum file size: 10MB. Saves metadata to database."
)
async def upload_policy(
    file: UploadFile = File(..., description="PDF file to upload"),
    db: AsyncSession = Depends(get_db)
) -> PolicyUploadResponse:
    """
    Upload a policy document and save metadata to database.
    
    Args:
        file: PDF file to upload
        db: Database session
        
    Returns:
        PolicyUploadResponse: Upload confirmation with file metadata
        
    Raises:
        HTTPException: If file validation fails or upload errors occur
    """
    
    # Validate file
    validate_pdf(file)
    
    # Generate unique ID and filename
    policy_id = f"pol_{uuid.uuid4().hex[:12]}"
    file_ext = os.path.splitext(file.filename)[1]
    stored_filename = f"{policy_id}{file_ext}"
    file_path = UPLOAD_DIR / stored_filename
    
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Calculate file hash
        file_hash = calculate_file_hash(content)
        
        # Check for duplicate files
        stmt = select(Policy).where(Policy.file_hash == file_hash, Policy.deleted_at.is_(None))
        result = await db.execute(stmt)
        existing_policy = result.scalar_one_or_none()
        
        if existing_policy:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"File already exists with policy_id: {existing_policy.policy_id}"
            )
        
        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create database record
        db_policy = Policy(
            policy_id=policy_id,
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_hash=file_hash,
            content_type=file.content_type,
            status=PolicyStatus.UPLOADED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_policy)
        await db.commit()
        await db.refresh(db_policy)
        
        # Create response
        return PolicyUploadResponse(
            id=db_policy.id,
            policy_id=db_policy.policy_id,
            filename=db_policy.filename,
            file_size=db_policy.file_size,
            content_type=db_policy.content_type,
            upload_timestamp=db_policy.created_at,
            storage_path=str(file_path.relative_to(Path.cwd())),
            status=db_policy.status.value
        )
        
    except HTTPException:
        # Clean up file if it was created
        if file_path.exists():
            file_path.unlink()
        raise
    except Exception as e:
        # Clean up file if it was created
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    finally:
        await file.close()


@router.get(
    "/list",
    response_model=PolicyListResponse,
    summary="List Uploaded Policies",
    description="Get a paginated list of uploaded policy documents with optional filtering."
)
async def list_policies(
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[PolicyStatusEnum] = Query(None, alias="status", description="Filter by status"),
    policy_type: Optional[PolicyTypeEnum] = Query(None, description="Filter by policy type"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    limit: int = Query(20, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
) -> PolicyListResponse:
    """
    List all uploaded policy documents with pagination and filtering.
    
    Args:
        db: Database session
        status_filter: Optional status filter
        policy_type: Optional policy type filter
        jurisdiction: Optional jurisdiction filter
        limit: Number of results per page
        offset: Number of results to skip
        
    Returns:
        PolicyListResponse: Paginated list of policies
    """
    
    # Build query
    query = select(Policy).where(Policy.deleted_at.is_(None))
    
    # Apply filters
    if status_filter:
        query = query.where(Policy.status == status_filter.value)
    if policy_type:
        query = query.where(Policy.policy_type == policy_type.value)
    if jurisdiction:
        query = query.where(Policy.jurisdiction.ilike(f"%{jurisdiction}%"))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Policy.created_at.desc()).limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    policies = result.scalars().all()
    
    return PolicyListResponse(
        policies=[PolicyPublic.model_validate(p) for p in policies],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{policy_id}",
    response_model=PolicyPublic,
    summary="Get Policy by ID",
    description="Retrieve a single policy document by its unique identifier."
)
async def get_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db)
) -> PolicyPublic:
    """
    Get a single policy by ID.
    
    Args:
        policy_id: Unique policy identifier
        db: Database session
        
    Returns:
        PolicyPublic: Policy details
        
    Raises:
        HTTPException: If policy not found
    """
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found"
        )
    
    return PolicyPublic.model_validate(policy)


@router.delete(
    "/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Policy",
    description="Soft delete a policy document (sets deleted_at timestamp)."
)
async def delete_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Soft delete a policy.
    
    Args:
        policy_id: Unique policy identifier
        db: Database session
        
    Raises:
        HTTPException: If policy not found
    """
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found"
        )
    
    # Soft delete
    policy.deleted_at = datetime.utcnow()
    policy.updated_at = datetime.utcnow()
    
    await db.commit()
