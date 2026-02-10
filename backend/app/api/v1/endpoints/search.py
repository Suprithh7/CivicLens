"""
API endpoints for semantic search.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from app.core.database import get_db
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SimilarChunksRequest,
    SimilarChunksResponse
)
from app.services.search_service import (
    semantic_search_policy,
    semantic_search_all,
    find_similar_chunks,
    SearchError
)
from app.services.faiss_service import FAISSError

router = APIRouter()


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic search across all policies",
    description="Search for relevant policy chunks across all policies using natural language queries."
)
async def search_all_policies(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Perform semantic search across all policies or a subset.
    
    Returns the most relevant chunks based on semantic similarity to the query.
    """
    try:
        results = await semantic_search_all(
            query=request.query,
            db=db,
            top_k=request.top_k,
            policy_ids=request.policy_ids
        )
        
        return {
            "query": request.query,
            "results": results,
            "total_results": len(results),
            "search_type": "all"
        }
    except (SearchError, FAISSError) as e:
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
                "message": "An unexpected error occurred during search",
                "error": str(e)
            }
        )


@router.post(
    "/{policy_id}/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic search within a policy",
    description="Search for relevant chunks within a specific policy using natural language queries."
)
async def search_policy(
    policy_id: str,
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Perform semantic search within a specific policy.
    
    Returns the most relevant chunks from the policy based on semantic similarity.
    """
    try:
        results = await semantic_search_policy(
            policy_id=policy_id,
            query=request.query,
            db=db,
            top_k=request.top_k
        )
        
        return {
            "query": request.query,
            "results": results,
            "total_results": len(results),
            "search_type": "policy"
        }
    except (SearchError, FAISSError) as e:
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
                "message": "An unexpected error occurred during search",
                "error": str(e)
            }
        )


@router.post(
    "/{policy_id}/similar-chunks/{chunk_index}",
    response_model=SimilarChunksResponse,
    status_code=status.HTTP_200_OK,
    summary="Find similar chunks",
    description="Find chunks similar to a given chunk within the same policy."
)
async def get_similar_chunks(
    policy_id: str,
    chunk_index: int,
    request: SimilarChunksRequest = SimilarChunksRequest(),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Find chunks similar to a reference chunk.
    
    Useful for discovering related content within a policy document.
    """
    try:
        results = await find_similar_chunks(
            policy_id=policy_id,
            chunk_index=chunk_index,
            db=db,
            top_k=request.top_k
        )
        
        return {
            "reference_chunk_index": chunk_index,
            "policy_id": policy_id,
            "results": results,
            "total_results": len(results)
        }
    except (SearchError, FAISSError) as e:
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
                "message": "An unexpected error occurred while finding similar chunks",
                "error": str(e)
            }
        )
