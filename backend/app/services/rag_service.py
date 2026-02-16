"""
RAG (Retrieval-Augmented Generation) service.
Orchestrates document retrieval and LLM-based answer generation.
"""

import logging
from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search_service import semantic_search_policy, semantic_search_all
from app.services.llm_service import (
    generate_completion,
    generate_completion_streaming,
    count_tokens,
    LLMError
)
from app.services.language_service import (
    detect_language,
    normalize_language_code,
    get_multilingual_instruction,
    get_language_name
)
from app.services.cache_service import (
    generate_cache_key,
    get_rag_cache,
    set_rag_cache
)
from app.services.evaluation_service import evaluate_output
from app.core.exceptions import CivicLensException

logger = logging.getLogger(__name__)


class RAGError(CivicLensException):
    """Exception raised when RAG operations fail."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details or {}
        )


def _construct_prompt(query: str, chunks: List[Dict], language: str = "en") -> tuple[str, str]:
    """
    Construct the LLM prompt from query and retrieved chunks.
    
    Args:
        query: User's question
        chunks: Retrieved document chunks with metadata
        language: Target language code for the response
        
    Returns:
        Tuple of (system_message, user_prompt)
    """
    language_name = get_language_name(language)
    language_instruction = get_multilingual_instruction(language)
    
    system_message = f"""You are a helpful AI assistant that answers questions about government policy documents.

Your role is to:
1. Provide accurate, concise answers based ONLY on the provided context
2. Cite specific sources when making claims
3. Acknowledge when information is not available in the context
4. Use clear, accessible language suitable for citizens{language_instruction}

Guidelines:
- If the context doesn't contain relevant information, say so clearly
- Don't make up or infer information not present in the context
- When referencing information, mention which source it comes from
- Be objective and factual"""

    # Build context from chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        policy_title = chunk.get("policy_title", "Unknown Policy")
        chunk_text = chunk.get("chunk_text", "")
        
        context_parts.append(
            f"[Source {i}: {policy_title}]\n{chunk_text}\n"
        )
    
    context = "\n".join(context_parts)
    
    user_prompt = f"""Context from policy documents:

{context}

Question: {query}

Please provide a clear and accurate answer based on the context above. If you reference information, mention which source number it comes from."""

    return system_message, user_prompt


def _format_response(
    answer: str,
    chunks: List[Dict],
    query: str,
    model: str,
    detected_language: str,
    response_language: str,
    include_evaluation: bool = True
) -> Dict:
    """
    Format the RAG response with answer and sources.
    
    Args:
        answer: Generated answer from LLM
        chunks: Retrieved chunks used as context
        query: Original query
        model: Model used for generation
        detected_language: Detected language from query
        response_language: Language of the response
        include_evaluation: Whether to include evaluation metrics
        
    Returns:
        Formatted response dictionary
    """
    sources = []
    for chunk in chunks:
        sources.append({
            "chunk_id": chunk.get("chunk_id"),
            "chunk_text": chunk.get("chunk_text"),
            "chunk_index": chunk.get("chunk_index"),
            "policy_id": chunk.get("policy_id"),
            "policy_title": chunk.get("policy_title"),
            "similarity_score": chunk.get("similarity_score"),
            "start_char": chunk.get("start_char"),
            "end_char": chunk.get("end_char")
        })
    
    response = {
        "answer": answer,
        "sources": sources,
        "query": query,
        "model_used": model,
        "timestamp": datetime.utcnow().isoformat(),
        "num_sources": len(sources),
        "detected_language": detected_language,
        "response_language": response_language
    }
    
    # Add evaluation metrics if requested
    if include_evaluation:
        try:
            evaluation_metrics = evaluate_output(
                answer=answer,
                query=query,
                sources=sources
            )
            response["evaluation"] = evaluation_metrics
            logger.info(
                f"Evaluation: confidence={evaluation_metrics['overall_confidence']:.2f}, "
                f"flags={len(evaluation_metrics['quality_flags'])}"
            )
        except Exception as e:
            logger.warning(f"Failed to evaluate output: {e}")
            # Don't fail the request if evaluation fails
            response["evaluation"] = None
    
    return response


async def answer_question(
    query: str,
    db: AsyncSession,
    policy_id: Optional[str] = None,
    top_k: int = 5,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    language: Optional[str] = None
) -> Dict:
    """
    Answer a question using RAG pipeline.
    
    Args:
        query: User's question
        db: Database session
        policy_id: Optional policy ID to limit search scope
        top_k: Number of chunks to retrieve
        model: LLM model to use
        temperature: Sampling temperature
        language: Target language code (auto-detects if not provided)
        
    Returns:
        Dictionary with answer and sources
        
    Raises:
        RAGError: If RAG pipeline fails
    """
    try:
        logger.info(f"Processing RAG query: '{query}' (policy_id={policy_id}, top_k={top_k})")
        
        # Generate cache key
        cache_key_data = {
            "query": query,
            "policy_id": policy_id or "all",
            "language": language or "auto",
            "top_k": top_k
        }
        cache_key = generate_cache_key(cache_key_data)
        
        # Check cache first
        cached_response = get_rag_cache(cache_key)
        if cached_response:
            logger.info(f"Cache HIT for RAG query: '{query[:50]}...'")
            # Add cache metadata
            cached_response["cached"] = True
            cached_response["cache_timestamp"] = cached_response["timestamp"]
            cached_response["timestamp"] = datetime.utcnow().isoformat()
            return cached_response
        
        logger.info(f"Cache MISS for RAG query: '{query[:50]}...'")
        
        # Detect or normalize language
        if language:
            detected_lang = normalize_language_code(language)
            logger.info(f"Using specified language: {detected_lang}")
        else:
            detected_lang = detect_language(query)
            logger.info(f"Auto-detected language: {detected_lang}")
        
        response_lang = detected_lang
        
        # Step 1: Retrieve relevant chunks
        if policy_id:
            search_results = await semantic_search_policy(
                policy_id=policy_id,
                query=query,
                db=db,
                top_k=top_k
            )
        else:
            search_results = await semantic_search_all(
                query=query,
                db=db,
                top_k=top_k
            )
        
        chunks = search_results
        logger.info(f"DEBUG: chunks type: {type(chunks)}")
        if chunks:
            logger.info(f"DEBUG: first chunk type: {type(chunks[0])}")
        
        if not chunks:
            logger.warning(f"No relevant chunks found for query: '{query}'")
            # Provide "no results" message in the detected language
            no_results_messages = {
                "en": "I couldn't find any relevant information in the policy documents to answer your question.",
                "es": "No pude encontrar información relevante en los documentos de políticas para responder a tu pregunta.",
                "fr": "Je n'ai pas trouvé d'informations pertinentes dans les documents de politique pour répondre à votre question.",
                "de": "Ich konnte keine relevanten Informationen in den Richtliniendokumenten finden, um Ihre Frage zu beantworten.",
                "hi": "मुझे आपके प्रश्न का उत्तर देने के लिए नीति दस्तावेज़ों में कोई प्रासंगिक जानकारी नहीं मिली।",
            }
            no_results_msg = no_results_messages.get(detected_lang, no_results_messages["en"])
            
            return {
                "answer": no_results_msg,
                "sources": [],
                "query": query,
                "model_used": model or "none",
                "timestamp": datetime.utcnow().isoformat(),
                "num_sources": 0,
                "detected_language": detected_lang,
                "response_language": response_lang
            }
        
        logger.info(f"Retrieved {len(chunks)} relevant chunks")
        
        # Step 2: Construct prompt with language instruction
        system_message, user_prompt = _construct_prompt(query, chunks, response_lang)
        
        # Log token count for monitoring
        prompt_tokens = count_tokens(system_message + user_prompt, model)
        logger.info(f"Prompt token count: {prompt_tokens}")
        
        # Step 3: Generate answer
        answer = await generate_completion(
            prompt=user_prompt,
            system_message=system_message,
            model=model,
            temperature=temperature
        )
        
        # Step 4: Format response
        response = _format_response(
            answer=answer,
            chunks=chunks,
            query=query,
            model=model or "default",
            detected_language=detected_lang,
            response_language=response_lang
        )
        
        # Add cache flag and store in cache
        response["cached"] = False
        set_rag_cache(cache_key, response)
        
        logger.info(f"Successfully generated answer ({len(answer)} chars)")
        
        return response
        
    except LLMError as e:
        logger.error(f"LLM error in RAG pipeline: {e}")
        raise RAGError(
            "Failed to generate answer",
            details={"error": str(e), "stage": "generation"}
        )
    except Exception as e:
        logger.error(f"Unexpected error in RAG pipeline: {e}")
        raise RAGError(
            "RAG pipeline failed",
            details={"error": str(e)}
        )


async def answer_question_streaming(
    query: str,
    db: AsyncSession,
    policy_id: Optional[str] = None,
    top_k: int = 5,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    language: Optional[str] = None
) -> AsyncGenerator[Dict, None]:
    """
    Answer a question using RAG pipeline with streaming response.
    
    Args:
        query: User's question
        db: Database session
        policy_id: Optional policy ID to limit search scope
        top_k: Number of chunks to retrieve
        model: LLM model to use
        temperature: Sampling temperature
        language: Target language code (auto-detects if not provided)
        
    Yields:
        Dictionaries with answer chunks and metadata
        
    Raises:
        RAGError: If RAG pipeline fails
    """
    try:
        logger.info(f"Processing streaming RAG query: '{query}' (policy_id={policy_id}, top_k={top_k})")
        
        # Detect or normalize language
        if language:
            detected_lang = normalize_language_code(language)
            logger.info(f"Using specified language: {detected_lang}")
        else:
            detected_lang = detect_language(query)
            logger.info(f"Auto-detected language: {detected_lang}")
        
        response_lang = detected_lang
        
        # Step 1: Retrieve relevant chunks
        if policy_id:
            search_results = await semantic_search_policy(
                policy_id=policy_id,
                query=query,
                db=db,
                top_k=top_k
            )
        else:
            search_results = await semantic_search_all(
                query=query,
                db=db,
                top_k=top_k
            )
        
        chunks = search_results
        
        # Yield sources first
        yield {
            "type": "sources",
            "sources": [
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "chunk_text": chunk.get("chunk_text"),
                    "chunk_index": chunk.get("chunk_index"),
                    "policy_id": chunk.get("policy_id"),
                    "policy_title": chunk.get("policy_title"),
                    "similarity_score": chunk.get("similarity_score"),
                    "start_char": chunk.get("start_char"),
                    "end_char": chunk.get("end_char")
                }
                for chunk in chunks
            ],
            "num_sources": len(chunks),
            "detected_language": detected_lang,
            "response_language": response_lang
        }
        
        if not chunks:
            logger.warning(f"No relevant chunks found for query: '{query}'")
            # Provide "no results" message in the detected language
            no_results_messages = {
                "en": "I couldn't find any relevant information in the policy documents to answer your question.",
                "es": "No pude encontrar información relevante en los documentos de políticas para responder a tu pregunta.",
                "fr": "Je n'ai pas trouvé d'informations pertinentes dans les documents de politique pour répondre à votre question.",
                "de": "Ich konnte keine relevanten Informationen in den Richtliniendokumenten finden, um Ihre Frage zu beantworten.",
                "hi": "मुझे आपके प्रश्न का उत्तर देने के लिए नीति दस्तावेज़ों में कोई प्रासंगिक जानकारी नहीं मिली।",
            }
            no_results_msg = no_results_messages.get(detected_lang, no_results_messages["en"])
            
            yield {
                "type": "answer",
                "content": no_results_msg,
                "done": True
            }
            return
        
        logger.info(f"Retrieved {len(chunks)} relevant chunks")
        
        # Step 2: Construct prompt with language instruction
        system_message, user_prompt = _construct_prompt(query, chunks, response_lang)
        
        # Step 3: Stream answer
        full_answer = ""
        async for chunk in generate_completion_streaming(
            prompt=user_prompt,
            system_message=system_message,
            model=model,
            temperature=temperature
        ):
            full_answer += chunk
            yield {
                "type": "answer",
                "content": chunk,
                "done": False
            }
        
        # Signal answer completion but keep stream open for evaluation
        yield {
            "type": "answer",
            "content": "",
            "done": True
        }
        
        logger.info("Streaming answer generation completed")
        
        # Step 4: Run evaluation
        try:
            evaluation_metrics = evaluate_output(
                answer=full_answer,
                query=query,
                sources=sources
            )
            
            yield {
                "type": "evaluation",
                "evaluation": evaluation_metrics
            }
            
            logger.info(
                f"Streamed evaluation: confidence={evaluation_metrics['overall_confidence']:.2f}, "
                f"flags={len(evaluation_metrics['quality_flags'])}"
            )
        except Exception as e:
            logger.warning(f"Failed to evaluate streaming output: {e}")
            # Yield empty evaluation or error? For now just log it.

        
    except LLMError as e:
        logger.error(f"LLM error in streaming RAG pipeline: {e}")
        raise RAGError(
            "Failed to generate streaming answer",
            details={"error": str(e), "stage": "generation"}
        )
    except Exception as e:
        logger.error(f"Unexpected error in streaming RAG pipeline: {e}")
        raise RAGError(
            "Streaming RAG pipeline failed",
            details={"error": str(e)}
        )
