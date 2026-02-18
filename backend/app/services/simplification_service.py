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
from app.services.language_service import (
    detect_language,
    normalize_language_code,
    get_language_name
)
from app.services.policy_simplification_prompts import (
    POLICY_SIMPLIFICATION_SYSTEM_MESSAGE,
    get_policy_explanation_prompt,
    get_eligibility_check_prompt,
    get_key_points_prompt,
    get_benefits_summary_prompt,
    get_application_process_prompt,
    get_scenario_based_prompt
)
from app.services.cache_service import (
    generate_cache_key,
    get_simplification_cache,
    set_simplification_cache
)
from app.services.evaluation_service import evaluate_output
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


def detect_uncertainty(response_text: str, policy_text: str) -> Dict:
    """
    Detect uncertainty indicators in LLM response and policy data.
    
    Args:
        response_text: The LLM's response
        policy_text: The original policy text
        
    Returns:
        Dictionary with uncertainty information:
        {
            "confidence": "high|medium|low|uncertain",
            "missing_info": [list of missing data points],
            "has_partial_answer": bool,
            "suggestions": [list of suggestions]
        }
    """
    uncertainty_indicators = {
        "low": [
            "i don't have enough information",
            "insufficient information",
            "cannot determine",
            "unclear",
            "not enough detail",
            "need more information",
            "missing information",
            "incomplete",
            "uncertain"
        ],
        "medium": [
            "based on the available information",
            "it appears",
            "it seems",
            "possibly",
            "might",
            "could be",
            "may be",
            "limited information"
        ]
    }
    
    response_lower = response_text.lower()
    
    # Check for explicit uncertainty markers
    low_confidence_count = sum(1 for phrase in uncertainty_indicators["low"] if phrase in response_lower)
    medium_confidence_count = sum(1 for phrase in uncertainty_indicators["medium"] if phrase in response_lower)
    
    # Check policy text length (very short = likely incomplete)
    policy_too_short = len(policy_text.strip()) < 200
    
    # Determine confidence level
    if low_confidence_count >= 2 or policy_too_short:
        confidence = "low"
    elif low_confidence_count >= 1 or medium_confidence_count >= 2:
        confidence = "medium"
    elif medium_confidence_count >= 1:
        confidence = "medium"
    else:
        confidence = "high"
    
    # Extract missing information if mentioned
    missing_info = []
    suggestions = []
    
    if "need more" in response_lower or "missing" in response_lower:
        has_partial_answer = True
        if policy_too_short:
            missing_info.append("Complete policy text")
            suggestions.append("Re-upload the policy document")
            suggestions.append("Verify the PDF is not corrupted")
    else:
        has_partial_answer = False
    
    # Add suggestions based on confidence
    if confidence in ["low", "medium"]:
        if not suggestions:
            suggestions.append("Provide more details about your situation")
            suggestions.append("Try a different scenario type if available")
    
    return {
        "confidence": confidence,
        "missing_info": missing_info,
        "has_partial_answer": has_partial_answer,
        "suggestions": suggestions
    }


def generate_fallback_response(
    policy_id: str,
    policy_title: Optional[str],
    explanation_type: str,
    reason: str = "insufficient_data"
) -> str:
    """
    Generate a helpful fallback response when AI cannot provide a complete answer.
    
    Args:
        policy_id: Policy identifier
        policy_title: Policy title if available
        explanation_type: Type of explanation requested
        reason: Reason for fallback (insufficient_data, corrupted, too_short, etc.)
        
    Returns:
        Fallback response text
    """
    title_text = f" for '{policy_title}'" if policy_title else ""
    
    if reason == "insufficient_data" or reason == "too_short":
        return f"""⚠️ **Limited Information Available**

I apologize, but I don't have enough information to provide a complete {explanation_type} explanation{title_text}.

**What's the issue?**
The policy document appears to be incomplete, very brief, or may not have been fully processed. I can only see a small portion of the text, which isn't sufficient to give you accurate guidance.

**What you can do:**
1. **Re-upload the document** - The PDF might be corrupted or incomplete
2. **Check the file** - Make sure you uploaded the complete policy document
3. **Try a different version** - If you have another copy of the policy, try uploading that
4. **Contact support** - If the issue persists, our team can help investigate

I want to make sure you get accurate information, so I'd rather be honest about limitations than provide potentially incorrect guidance."""

    elif reason == "out_of_scope":
        return f"""ℹ️ **This Policy May Not Apply to Your Scenario**

Based on my analysis of the policy{title_text}, it doesn't appear to have specific provisions for your selected scenario.

**What this means:**
The policy may be designed for a different audience or situation than what you've described.

**What you can do:**
1. **Try a different scenario** - Select another option that might better match the policy
2. **Search for related policies** - There may be other policies better suited to your situation
3. **Read the general explanation** - Try the "general explanation" option to understand the policy's overall purpose

**Need help?**
If you believe this policy should apply to your situation, consider contacting the relevant government agency directly for clarification."""

    else:
        return f"""⚠️ **Unable to Process Request**

I encountered an issue while trying to explain this policy{title_text}.

**What you can do:**
1. Try again in a few moments
2. Try a different explanation type
3. Contact support if the problem continues

I apologize for the inconvenience!"""


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
    temperature: Optional[float] = None,
    language: Optional[str] = None,
    scenario_type: Optional[str] = None,
    scenario_details: Optional[str] = None
) -> Dict:
    """
    Generate a simplified explanation of a policy document.
    
    Args:
        policy_id: Policy identifier
        db: Database session
        explanation_type: Type of explanation (explanation, eligibility, key_points, benefits, application, scenario)
        user_situation: User's situation for eligibility checks
        focus_area: Specific aspect to focus on
        max_points: Maximum number of key points (for key_points type)
        model: LLM model to use
        temperature: Sampling temperature
        language: Target language code (auto-detects if not provided)
        scenario_type: User scenario type (required for scenario type)
        scenario_details: Additional scenario details (optional for scenario type)
        
    Returns:
        Dictionary with simplified explanation and metadata
        
    Raises:
        SimplificationError: If simplification fails
    """
    try:
        logger.info(
            f"Simplifying policy {policy_id} "
            f"(type={explanation_type}, language={language or 'auto'})"
        )
        
        # Generate cache key
        cache_key_data = {
            "policy_id": policy_id,
            "explanation_type": explanation_type,
            "language": language or "auto",
            "scenario_type": scenario_type,
            "scenario_details": scenario_details,
            "user_situation": user_situation,
            "focus_area": focus_area,
            "max_points": max_points
        }
        cache_key = generate_cache_key(cache_key_data)
        
        # Check cache first
        cached_response = get_simplification_cache(cache_key)
        if cached_response:
            logger.info(f"Cache HIT for policy {policy_id} ({explanation_type})")
            # Add cache metadata
            cached_response["cached"] = True
            cached_response["cache_timestamp"] = cached_response["timestamp"]
            cached_response["timestamp"] = datetime.utcnow().isoformat()
            return cached_response
        
        logger.info(f"Cache MISS for policy {policy_id} ({explanation_type})")
        
        # Detect or normalize language
        if language:
            detected_lang = normalize_language_code(language)
            logger.info(f"Using specified language: {detected_lang}")
        else:
            # Try to detect from user_situation or focus_area
            text_for_detection = user_situation or focus_area or ""
            if text_for_detection:
                detected_lang = detect_language(text_for_detection)
                logger.info(f"Auto-detected language from input: {detected_lang}")
            else:
                detected_lang = "en"  # Default to English
                logger.info("No text for language detection, defaulting to English")
        
        response_lang = detected_lang
        
        # Get policy text
        policy_text, policy_title = await get_policy_text(policy_id, db)
        
        # Generate appropriate prompt based on explanation type
        if explanation_type == "explanation":
            prompt = get_policy_explanation_prompt(
                policy_text=policy_text,
                policy_title=policy_title,
                focus_area=focus_area,
                language=response_lang
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
                policy_title=policy_title,
                language=response_lang
            )
            # Use lower temperature for more factual responses
            temp = temperature if temperature is not None else 0.3
            
        elif explanation_type == "key_points":
            prompt = get_key_points_prompt(
                policy_text=policy_text,
                max_points=max_points,
                language=response_lang
            )
            temp = temperature if temperature is not None else 0.5
            
        elif explanation_type == "benefits":
            prompt = get_benefits_summary_prompt(
                policy_text=policy_text,
                language=response_lang
            )
            temp = temperature if temperature is not None else 0.6
            
        elif explanation_type == "application":
            prompt = get_application_process_prompt(
                policy_text=policy_text,
                language=response_lang
            )
            temp = temperature if temperature is not None else 0.5
            
        elif explanation_type == "scenario":
            if not scenario_type:
                raise SimplificationError(
                    "scenario_type is required for scenario-based explanations",
                    details={"explanation_type": explanation_type}
                )
            prompt = get_scenario_based_prompt(
                policy_text=policy_text,
                scenario_type=scenario_type,
                policy_title=policy_title,
                scenario_details=scenario_details,
                language=response_lang
            )
            # Use moderate temperature for balanced factual + helpful tone
            temp = temperature if temperature is not None else 0.5
            
        else:
            raise SimplificationError(
                f"Invalid explanation type: {explanation_type}",
                details={
                    "explanation_type": explanation_type,
                    "valid_types": ["explanation", "eligibility", "key_points", "benefits", "application", "scenario"]
                }
            )
        
        # Generate simplified explanation
        system_msg = POLICY_SIMPLIFICATION_SYSTEM_MESSAGE(response_lang)
        simplified_text = await generate_completion(
            prompt=prompt,
            system_message=system_msg,
            model=model,
            temperature=temp
        )
        
        # Detect uncertainty and confidence level
        uncertainty_info = detect_uncertainty(simplified_text, policy_text)
        
        # Check if policy text is too short - use fallback if needed
        if len(policy_text.strip()) < 200:
            logger.warning(f"Policy text too short ({len(policy_text)} chars), using fallback response")
            simplified_text = generate_fallback_response(
                policy_id=policy_id,
                policy_title=policy_title,
                explanation_type=explanation_type,
                reason="too_short"
            )
            uncertainty_info = {
                "confidence": "low",
                "missing_info": ["Complete policy text"],
                "has_partial_answer": False,
                "suggestions": [
                    "Re-upload the policy document",
                    "Verify the PDF is not corrupted",
                    "Try uploading a different version of the policy"
                ]
            }
        
        # Run evaluation on the simplified text
        evaluation_metrics = None
        try:
            # For simplification, we don't have "sources" in the same way as RAG
            # But we can pass the policy text as context
            evaluation_metrics = evaluate_output(
                answer=simplified_text,
                query=f"Explain this policy ({explanation_type})",
                sources=[],  # No chunked sources for simplification
                context={"policy_text": policy_text}
            )
            logger.info(
                f"Simplification evaluation: confidence={evaluation_metrics['overall_confidence']:.2f}, "
                f"flags={len(evaluation_metrics['quality_flags'])}"
            )
        except Exception as e:
            logger.warning(f"Failed to evaluate simplification output: {e}")
        
        # Format response with uncertainty information and evaluation
        response = {
            "policy_id": policy_id,
            "policy_title": policy_title,
            "explanation_type": explanation_type,
            "simplified_text": simplified_text,
            "model_used": model or "default",
            "timestamp": datetime.utcnow().isoformat(),
            "detected_language": detected_lang,
            "response_language": response_lang,
            "confidence_level": uncertainty_info["confidence"],
            "missing_information": uncertainty_info["missing_info"] if uncertainty_info["missing_info"] else None,
            "is_partial_answer": uncertainty_info["has_partial_answer"],
            "suggestions": uncertainty_info["suggestions"] if uncertainty_info["suggestions"] else None,
            "evaluation": evaluation_metrics,
            "cached": False
        }
        
        # Store in cache
        set_simplification_cache(cache_key, response)
        
        logger.info(
            f"Generated {explanation_type} explanation for policy {policy_id} "
            f"(confidence: {uncertainty_info['confidence']}, {len(simplified_text)} chars)"
        )
        
        return response
        
    except LLMError as e:
        logger.error(f"LLM error during simplification: {e}")
        raise SimplificationError(
            "Failed to generate simplified explanation",
            details={"error": str(e), "stage": "generation", "upstream_details": e.details}
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
