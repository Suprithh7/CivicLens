"""
Policy endpoints for document upload and management.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

from app.schemas.policy import (
    PolicyUploadResponse, 
    PolicyPublic, 
    PolicyListResponse,
    PolicyStatusEnum,
    PolicyTypeEnum,
    TextExtractionResponse,
    ExtractedTextResponse
)
from app.models.policy import Policy, PolicyStatus
from app.core.dependencies import get_db
from app.constants import (
    POLICY_UPLOAD_DIR,
    MAX_FILE_SIZE_BYTES,
    ERROR_POLICY_NOT_FOUND,
    ERROR_POLICY_ALREADY_EXISTS,
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    SUCCESS_TEXT_EXTRACTION_STARTED,
    ERROR_NO_EXTRACTED_TEXT,
)
from app.utils.file_utils import (
    validate_pdf,
    validate_file_size,
    calculate_file_hash,
    generate_unique_id,
    sanitize_filename,
)
from app.services.text_extraction import (
    process_policy_text_extraction,
    get_extracted_text,
    TextExtractionError
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Ensure upload directory exists
POLICY_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)




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
    
    logger.info(f"Starting policy upload: {file.filename}")
    
    # Validate file type
    validate_pdf(file)
    logger.debug(f"File validation passed for: {file.filename}")
    
    # Generate unique ID and sanitize filename
    policy_id = generate_unique_id()
    file_ext = Path(file.filename).suffix
    stored_filename = f"{policy_id}{file_ext}"
    file_path = POLICY_UPLOAD_DIR / stored_filename
    
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        logger.debug(f"File read successfully: {file_size} bytes")
        
        # Validate file size
        validate_file_size(file_size, MAX_FILE_SIZE_BYTES)
        
        # Calculate file hash
        file_hash = calculate_file_hash(content)
        
        # Check for duplicate files
        stmt = select(Policy).where(Policy.file_hash == file_hash, Policy.deleted_at.is_(None))
        result = await db.execute(stmt)
        existing_policy = result.scalar_one_or_none()
        
        if existing_policy:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{ERROR_POLICY_ALREADY_EXISTS}: {existing_policy.policy_id}"
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
        
        logger.info(f"Policy uploaded successfully: {policy_id} ({file.filename})")
        
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
        logger.warning(f"Policy upload failed (validation): {file.filename}")
        raise
    except Exception as e:
        # Clean up file if it was created
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Policy upload failed: {file.filename}", exc_info=True)
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
    limit: int = Query(DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Number of results per page"),
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
    logger.info(f"Listing policies: limit={limit}, offset={offset}, status={status_filter}, type={policy_type}")
    
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
    
    logger.info(f"Found {len(policies)} policies (total: {total})")
    
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
    logger.info(f"Fetching policy: {policy_id}")
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        logger.warning(f"Policy not found: {policy_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found"
        )
    
    logger.debug(f"Policy found: {policy_id}")
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
    logger.info(f"Deleting policy: {policy_id}")
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        logger.warning(f"Policy not found for deletion: {policy_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID '{policy_id}' not found"
        )
    
    # Soft delete
    policy.deleted_at = datetime.utcnow()
    policy.updated_at = datetime.utcnow()
    
    await db.commit()
    logger.info(f"Policy deleted successfully: {policy_id}")


@router.post(
    "/{policy_id}/extract-text",
    response_model=TextExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Text from Policy PDF",
    description="Trigger text extraction from a policy PDF document. Creates a processing record and extracts raw text."
)
async def extract_policy_text(
    policy_id: str,
    force: bool = Query(False, description="Force re-extraction even if already extracted"),
    db: AsyncSession = Depends(get_db)
) -> TextExtractionResponse:
    """
    Extract text from a policy PDF.
    
    Args:
        policy_id: Unique policy identifier
        force: If True, re-extract even if already extracted
        db: Database session
        
    Returns:
        TextExtractionResponse: Extraction result with text preview
        
    Raises:
        HTTPException: If policy not found or extraction fails
    """
    logger.info(f"Text extraction requested for policy: {policy_id} (force={force})")
    
    try:
        result = await process_policy_text_extraction(policy_id, db, force=force)
        return TextExtractionResponse(**result)
    except TextExtractionError as e:
        logger.error(f"Text extraction error: {e.message}", exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error during text extraction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text extraction failed: {str(e)}"
        )


@router.get(
    "/{policy_id}/text",
    response_model=ExtractedTextResponse,
    summary="Get Extracted Text",
    description="Retrieve the full extracted text content from a policy document."
)
async def get_policy_text(
    policy_id: str,
    db: AsyncSession = Depends(get_db)
) -> ExtractedTextResponse:
    """
    Get extracted text for a policy.
    
    Args:
        policy_id: Unique policy identifier
        db: Database session
        
    Returns:
        ExtractedTextResponse: Full extracted text and metadata
        
    Raises:
        HTTPException: If policy not found or text not extracted
    """
    logger.info(f"Retrieving extracted text for policy: {policy_id}")
    
    try:
        # Get policy
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
        
        # Get extracted text
        extracted_text = await get_extracted_text(policy_id, db)
        
        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_NO_EXTRACTED_TEXT
            )
        
        return ExtractedTextResponse(
            policy_id=policy_id,
            filename=policy.filename,
            extracted_text=extracted_text,
            character_count=len(extracted_text),
            word_count=len(extracted_text.split()),
            extraction_timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving extracted text: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve extracted text: {str(e)}"
        )

