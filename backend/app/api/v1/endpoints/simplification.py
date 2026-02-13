"""
Policy simplification API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.simplification import SimplificationRequest, SimplificationResponse
from app.services.simplification_service import simplify_policy, SimplificationError
from app.services.llm_service import LLMError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/explain",
    response_model=SimplificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get simplified policy explanation",
    description="Transform complex policy documents into accessible, plain-language explanations. "
                "Supports multiple explanation types: general explanation, eligibility check, "
                "key points, benefits summary, and application process."
)
async def explain_policy(
    request: SimplificationRequest,
    db: AsyncSession = Depends(get_db)
) -> SimplificationResponse:
    """
    Generate a simplified explanation of a policy document.
    
    This endpoint:
    1. Retrieves the policy text from the database
    2. Generates an appropriate prompt based on the explanation type
    3. Uses an LLM to create a plain-language explanation
    4. Returns the simplified text with metadata
    
    Args:
        request: Simplification request with policy_id and parameters
        db: Database session
        
    Returns:
        Simplified explanation with metadata
        
    Raises:
        HTTPException: If simplification fails
    """
    try:
        logger.info(
            f"Received simplification request for policy '{request.policy_id}' "
            f"with type '{request.explanation_type}'"
        )
        
        # Validate eligibility type requirements
        if request.explanation_type == "eligibility" and not request.user_situation:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "user_situation is required for eligibility checks",
                    "explanation_type": request.explanation_type
                }
            )
        
        # Generate simplified explanation
        response = await simplify_policy(
            policy_id=request.policy_id,
            db=db,
            explanation_type=request.explanation_type.value,
            user_situation=request.user_situation,
            focus_area=request.focus_area,
            max_points=request.max_points,
            model=request.model,
            temperature=request.temperature
        )
        
        return SimplificationResponse(**response)
        
    except SimplificationError as e:
        logger.error(f"Simplification error: {e}")
        
        # Check if it's a "not found" error
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Policy not found",
                    "policy_id": request.policy_id
                }
            )
        
        # Check if it's a "no text available" error
        if "no text available" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Policy text not available. Policy must be processed first.",
                    "policy_id": request.policy_id,
                    "details": e.details
                }
            )
        
        # Generic simplification error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to simplify policy",
                "error": str(e),
                "details": e.details
            }
        )
        
    except LLMError as e:
        logger.error(f"LLM error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "LLM service error",
                "error": str(e),
                "details": e.details
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in explain endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to process simplification request",
                "error": str(e)
            }
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Check simplification service health",
    description="Check if the simplification service is properly configured"
)
async def health_check():
    """
    Check simplification service health.
    
    Returns:
        Health status information
    """
    from app.config import settings
    
    health_status = {
        "status": "healthy",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "api_key_configured": bool(settings.LLM_API_KEY),
        "available_explanation_types": [
            "explanation",
            "eligibility",
            "key_points",
            "benefits",
            "application"
        ]
    }
    
    if not settings.LLM_API_KEY:
        health_status["status"] = "degraded"
        health_status["warning"] = "LLM API key not configured"
    
    return health_status
