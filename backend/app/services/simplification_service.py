"""
Policy simplification service.
Transforms complex policy documents into accessible, plain-language explanations.
"""

import logging
from typing import Optional, Dict
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.policy import Policy, PolicyProcessing, ProcessingStage, ProcessingStatus, PolicyChunk
from app.services.llm_service import generate_completion, LLMError
from app.services.policy_simplification_prompts import (
    POLICY_SIMPLIFICATION_SYSTEM_MESSAGE,
    get_policy_explanation_prompt,
    get_eligibility_check_prompt,
    get_key_points_prompt,
    get_benefits_summary_prompt,
    get_application_process_prompt
)
from app.core.exceptions import CivicLensException

logger = logging.getLogger(__name__)


class SimplificationError(CivicLensException):
    """Exception raised when policy simplification fails."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details or {}
        )


async def get_policy_text(policy_id: str, db: AsyncSession) -> tuple[str, Optional[str]]:
    """
    Retrieve policy text for simplification.
    
    Tries to get text from:
    1. Policy chunks (if available)
    2. Text extraction processing record
    
    Args:
        policy_id: Policy identifier
        db: Database session
        
    Returns:
        Tuple of (policy_text, policy_title)
        
    Raises:
        SimplificationError: If policy not found or no text available
    """
    # Get policy
    result = await db.execute(
        select(Policy).where(Policy.policy_id == policy_id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise SimplificationError(
            f"Policy not found: {policy_id}",
            details={"policy_id": policy_id}
        )
    
    policy_title = policy.title
    
    # Try to get text from chunks first (preferred)
    chunks_result = await db.execute(
        select(PolicyChunk)
        .where(PolicyChunk.policy_id == policy.id)
        .order_by(PolicyChunk.chunk_index)
    )
    chunks = chunks_result.scalars().all()
    
    if chunks:
        # Combine all chunks to get full text
        policy_text = "\n\n".join(chunk.chunk_text for chunk in chunks)
        logger.info(f"Retrieved {len(chunks)} chunks for policy {policy_id}")
        return policy_text, policy_title
    
    # Fallback: Try to get from text extraction processing record
    processing_result = await db.execute(
        select(PolicyProcessing)
        .where(
            PolicyProcessing.policy_id == policy.id,
            PolicyProcessing.stage == ProcessingStage.TEXT_EXTRACTION,
            PolicyProcessing.status == ProcessingStatus.COMPLETED
        )
    )
    processing = processing_result.scalar_one_or_none()
    
    if processing and processing.result_data:
        extracted_text = processing.result_data.get("extracted_text")
        if extracted_text:
            logger.info(f"Retrieved extracted text for policy {policy_id}")
            return extracted_text, policy_title
    
    # No text available
    raise SimplificationError(
        f"No text available for policy {policy_id}. Policy must be processed first.",
        details={
            "policy_id": policy_id,
            "status": policy.status.value,
            "has_chunks": len(chunks) > 0
        }
    )


async def simplify_policy(
    policy_id: str,
    db: AsyncSession,
    explanation_type: str = "explanation",
    user_situation: Optional[str] = None,
    focus_area: Optional[str] = None,
    max_points: int = 5,
    model: Optional[str] = None,
    temperature: Optional[float] = None
) -> Dict:
    """
    Generate a simplified explanation of a policy document.
    
    Args:
        policy_id: Policy identifier
        db: Database session
        explanation_type: Type of explanation (explanation, eligibility, key_points, benefits, application)
        user_situation: User's situation for eligibility checks
        focus_area: Specific aspect to focus on
        max_points: Maximum number of key points (for key_points type)
        model: LLM model to use
        temperature: Sampling temperature
        
    Returns:
        Dictionary with simplified explanation and metadata
        
    Raises:
        SimplificationError: If simplification fails
    """
    try:
        logger.info(f"Simplifying policy {policy_id} with type '{explanation_type}'")
        
        # Get policy text
        policy_text, policy_title = await get_policy_text(policy_id, db)
        
        # Generate appropriate prompt based on explanation type
        if explanation_type == "explanation":
            prompt = get_policy_explanation_prompt(
                policy_text=policy_text,
                policy_title=policy_title,
                focus_area=focus_area
            )
            # Use moderate temperature for balanced creativity and accuracy
            temp = temperature if temperature is not None else 0.7
            
        elif explanation_type == "eligibility":
            if not user_situation:
                raise SimplificationError(
                    "user_situation is required for eligibility checks",
                    details={"explanation_type": explanation_type}
                )
            prompt = get_eligibility_check_prompt(
                policy_text=policy_text,
                user_situation=user_situation,
                policy_title=policy_title
            )
            # Use lower temperature for more factual responses
            temp = temperature if temperature is not None else 0.3
            
        elif explanation_type == "key_points":
            prompt = get_key_points_prompt(
                policy_text=policy_text,
                max_points=max_points
            )
            temp = temperature if temperature is not None else 0.5
            
        elif explanation_type == "benefits":
            prompt = get_benefits_summary_prompt(policy_text=policy_text)
            temp = temperature if temperature is not None else 0.6
            
        elif explanation_type == "application":
            prompt = get_application_process_prompt(policy_text=policy_text)
            temp = temperature if temperature is not None else 0.5
            
        else:
            raise SimplificationError(
                f"Invalid explanation type: {explanation_type}",
                details={
                    "explanation_type": explanation_type,
                    "valid_types": ["explanation", "eligibility", "key_points", "benefits", "application"]
                }
            )
        
        # Generate simplified explanation
        simplified_text = await generate_completion(
            prompt=prompt,
            system_message=POLICY_SIMPLIFICATION_SYSTEM_MESSAGE,
            model=model,
            temperature=temp
        )
        
        # Format response
        response = {
            "policy_id": policy_id,
            "policy_title": policy_title,
            "explanation_type": explanation_type,
            "simplified_text": simplified_text,
            "model_used": model or "default",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Successfully simplified policy {policy_id} ({len(simplified_text)} chars)")
        
        return response
        
    except LLMError as e:
        logger.error(f"LLM error during simplification: {e}")
        raise SimplificationError(
            "Failed to generate simplified explanation",
            details={"error": str(e), "stage": "generation"}
        )
    except SimplificationError:
        # Re-raise SimplificationErrors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during simplification: {e}")
        raise SimplificationError(
            "Policy simplification failed",
            details={"error": str(e)}
        )
