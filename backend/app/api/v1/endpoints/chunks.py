"""
Chunk endpoints for text chunking operations.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.schemas.chunk import (
    ChunkPublic,
    ChunkListResponse,
    ChunkingRequest,
    ChunkingResponse,
)
from app.core.dependencies import get_db
from app.constants import (
    ERROR_CHUNK_NOT_FOUND,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
)
from app.services.text_chunking import (
    process_policy_chunking,
    get_policy_chunks,
    get_chunk_by_index,
    get_chunk_count,
    ChunkingError
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{policy_id}/chunk",
    response_model=ChunkingResponse,
    status_code=status.HTTP_200_OK,
    summary="Chunk Policy Text",
    description="Break down policy text into manageable chunks with configurable size and overlap."
)
async def chunk_policy_text(
    policy_id: str,
    chunk_size: int = Query(DEFAULT_CHUNK_SIZE, ge=100, le=5000, description="Target chunk size in characters"),
    overlap: int = Query(DEFAULT_CHUNK_OVERLAP, ge=0, le=500, description="Overlap between chunks in characters"),
    force: bool = Query(False, description="Force re-chunking even if already chunked"),
    db: AsyncSession = Depends(get_db)
) -> ChunkingResponse:
    """
    Chunk policy text into smaller segments.
    
    Args:
        policy_id: Unique policy identifier
        chunk_size: Target size for each chunk
        overlap: Number of characters to overlap between chunks
        force: Force re-chunking if already chunked
        db: Database session
        
    Returns:
        ChunkingResponse: Chunking statistics and metadata
        
    Raises:
        HTTPException: If policy not found or chunking fails
    """
    logger.info(f"Chunking requested for policy: {policy_id}, size={chunk_size}, overlap={overlap}, force={force}")
    
    try:
        result = await process_policy_chunking(
            policy_id=policy_id,
            db=db,
            chunk_size=chunk_size,
            overlap=overlap,
            force=force
        )
        return ChunkingResponse(**result)
    except ChunkingError as e:
        logger.error(f"Chunking error: {e.message}", exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error during chunking: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chunking failed: {str(e)}"
        )


@router.get(
    "/{policy_id}/chunks",
    response_model=ChunkListResponse,
    summary="List Policy Chunks",
    description="Retrieve all chunks for a policy document with pagination."
)
async def list_policy_chunks(
    policy_id: str,
    limit: int = Query(DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Number of chunks per page"),
    offset: int = Query(0, ge=0, description="Number of chunks to skip"),
    db: AsyncSession = Depends(get_db)
) -> ChunkListResponse:
    """
    List all chunks for a policy.
    
    Args:
        policy_id: Unique policy identifier
        limit: Maximum number of chunks to return
        offset: Number of chunks to skip
        db: Database session
        
    Returns:
        ChunkListResponse: Paginated list of chunks
        
    Raises:
        HTTPException: If policy not found
    """
    logger.info(f"Listing chunks for policy: {policy_id}, limit={limit}, offset={offset}")
    
    try:
        chunks = await get_policy_chunks(policy_id, db, limit=limit, offset=offset)
        total = await get_chunk_count(policy_id, db)
        
        return ChunkListResponse(
            chunks=[ChunkPublic.model_validate(c) for c in chunks],
            total=total,
            limit=limit,
            offset=offset,
            policy_id=policy_id
        )
    except ChunkingError as e:
        logger.error(f"Error listing chunks: {e.message}", exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error listing chunks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list chunks: {str(e)}"
        )


@router.get(
    "/{policy_id}/chunks/{chunk_index}",
    response_model=ChunkPublic,
    summary="Get Chunk by Index",
    description="Retrieve a specific chunk by its index."
)
async def get_chunk(
    policy_id: str,
    chunk_index: int,
    db: AsyncSession = Depends(get_db)
) -> ChunkPublic:
    """
    Get a specific chunk by index.
    
    Args:
        policy_id: Unique policy identifier
        chunk_index: Index of the chunk to retrieve
        db: Database session
        
    Returns:
        ChunkPublic: Chunk data
        
    Raises:
        HTTPException: If chunk not found
    """
    logger.info(f"Retrieving chunk {chunk_index} for policy: {policy_id}")
    
    try:
        chunk = await get_chunk_by_index(policy_id, chunk_index, db)
        
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{ERROR_CHUNK_NOT_FOUND}: chunk_index={chunk_index}"
            )
        
        return ChunkPublic.model_validate(chunk)
    except HTTPException:
        raise
    except ChunkingError as e:
        logger.error(f"Error retrieving chunk: {e.message}", exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving chunk: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chunk: {str(e)}"
        )
