"""
Response utility functions.
Provides helpers for building standardized API responses.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime


def success_response(
    message: str,
    data: Optional[Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Build a standardized success response.
    
    Args:
        message: Success message
        data: Optional data payload
        **kwargs: Additional fields to include in response
        
    Returns:
        Standardized success response dictionary
    """
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    response.update(kwargs)
    return response


def error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Build a standardized error response.
    
    Args:
        message: Error message
        error_code: Optional error code
        details: Optional error details
        **kwargs: Additional fields to include in response
        
    Returns:
        Standardized error response dictionary
    """
    response = {
        "success": False,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details is not None:
        response["details"] = details
    
    response.update(kwargs)
    return response


def paginated_response(
    items: List[Any],
    total: int,
    limit: int,
    offset: int,
    **kwargs
) -> Dict[str, Any]:
    """
    Build a standardized paginated response.
    
    Args:
        items: List of items for current page
        total: Total number of items
        limit: Number of items per page
        offset: Number of items skipped
        **kwargs: Additional fields to include in response
        
    Returns:
        Standardized paginated response dictionary
    """
    response = {
        "items": items,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "count": len(items),
            "has_more": (offset + len(items)) < total
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response.update(kwargs)
    return response
