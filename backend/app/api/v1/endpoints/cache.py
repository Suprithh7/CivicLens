"""
Cache management endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

from app.services.cache_service import get_cache_stats, clear_cache

router = APIRouter()


class ClearCacheRequest(BaseModel):
    """Request model for clearing cache."""
    cache_type: str = "all"  # "all", "simplification", or "rag"


@router.get("/stats")
async def get_cache_statistics():
    """
    Get cache statistics including hit rates and cost savings.
    
    Returns:
        Cache statistics for simplification and RAG caches
    """
    try:
        stats = get_cache_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cache statistics: {str(e)}"
        )


@router.post("/clear")
async def clear_cache_endpoint(request: ClearCacheRequest):
    """
    Clear cache(s).
    
    Admin endpoint to manually clear caches.
    
    Args:
        request: Cache clear request with cache_type
        
    Returns:
        Confirmation message
    """
    try:
        if request.cache_type not in ["all", "simplification", "rag"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cache_type: {request.cache_type}. Must be 'all', 'simplification', or 'rag'"
            )
        
        result = clear_cache(request.cache_type)
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )
