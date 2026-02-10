"""
API endpoints for vector embedding generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from app.core.database import get_db
from app.schemas.chunk import EmbeddingRequest, EmbeddingResponse, EmbeddingStatusResponse
from app.services.embedding_service import (
    process_policy_embeddings,
    get_embedding_status,
    EmbeddingError
)

router = APIRouter()


@router.post(
    "/{policy_id}/embeddings",
    response_model=EmbeddingResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate embeddings for policy chunks",
    description="Generate vector embeddings for all chunks of a policy document using sentence-transformers."
)
async def generate_policy_embeddings(
    policy_id: str,
    request: EmbeddingRequest = EmbeddingRequest(),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Generate vector embeddings for all chunks of a policy.
    
    The policy must be chunked before embeddings can be generated.
    Use force=true to regenerate embeddings if they already exist.
    """
    try:
        result = await process_policy_embeddings(
            policy_id=policy_id,
            db=db,
            force=request.force,
            batch_size=request.batch_size
        )
        return result
    except EmbeddingError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred during embedding generation",
                "error": str(e)
            }
        )


@router.get(
    "/{policy_id}/embeddings/status",
    response_model=EmbeddingStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get embedding generation status",
    description="Check the status of embedding generation for a policy."
)
async def get_policy_embedding_status(
    policy_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get the current status of embedding generation for a policy.
    
    Returns information about whether embeddings have been generated,
    are in progress, or have failed.
    """
    try:
        status_info = await get_embedding_status(
            policy_id=policy_id,
            db=db
        )
        return status_info
    except EmbeddingError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred while checking embedding status",
                "error": str(e)
            }
        )
