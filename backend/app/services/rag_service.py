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


def _construct_prompt(query: str, chunks: List[Dict]) -> tuple[str, str]:
    """
    Construct the LLM prompt from query and retrieved chunks.
    
    Args:
        query: User's question
        chunks: Retrieved document chunks with metadata
        
    Returns:
        Tuple of (system_message, user_prompt)
    """
    system_message = """You are a helpful AI assistant that answers questions about government policy documents.

Your role is to:
1. Provide accurate, concise answers based ONLY on the provided context
2. Cite specific sources when making claims
3. Acknowledge when information is not available in the context
4. Use clear, accessible language suitable for citizens

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
    model: str
) -> Dict:
    """
    Format the RAG response with answer and sources.
    
    Args:
        answer: Generated answer from LLM
        chunks: Retrieved chunks used as context
        query: Original query
        model: Model used for generation
        
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
    
    return {
        "answer": answer,
        "sources": sources,
        "query": query,
        "model_used": model,
        "timestamp": datetime.utcnow().isoformat(),
        "num_sources": len(sources)
    }


async def answer_question(
    query: str,
    db: AsyncSession,
    policy_id: Optional[str] = None,
    top_k: int = 5,
    model: Optional[str] = None,
    temperature: Optional[float] = None
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
        
    Returns:
        Dictionary with answer and sources
        
    Raises:
        RAGError: If RAG pipeline fails
    """
    try:
        logger.info(f"Processing RAG query: '{query}' (policy_id={policy_id}, top_k={top_k})")
        
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
        
        chunks = search_results.get("results", [])
        
        if not chunks:
            logger.warning(f"No relevant chunks found for query: '{query}'")
            return {
                "answer": "I couldn't find any relevant information in the policy documents to answer your question.",
                "sources": [],
                "query": query,
                "model_used": model or "none",
                "timestamp": datetime.utcnow().isoformat(),
                "num_sources": 0
            }
        
        logger.info(f"Retrieved {len(chunks)} relevant chunks")
        
        # Step 2: Construct prompt
        system_message, user_prompt = _construct_prompt(query, chunks)
        
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
            model=model or "default"
        )
        
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
    temperature: Optional[float] = None
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
        
    Yields:
        Dictionaries with answer chunks and metadata
        
    Raises:
        RAGError: If RAG pipeline fails
    """
    try:
        logger.info(f"Processing streaming RAG query: '{query}' (policy_id={policy_id}, top_k={top_k})")
        
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
        
        chunks = search_results.get("results", [])
        
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
            "num_sources": len(chunks)
        }
        
        if not chunks:
            logger.warning(f"No relevant chunks found for query: '{query}'")
            yield {
                "type": "answer",
                "content": "I couldn't find any relevant information in the policy documents to answer your question.",
                "done": True
            }
            return
        
        logger.info(f"Retrieved {len(chunks)} relevant chunks")
        
        # Step 2: Construct prompt
        system_message, user_prompt = _construct_prompt(query, chunks)
        
        # Step 3: Stream answer
        async for chunk in generate_completion_streaming(
            prompt=user_prompt,
            system_message=system_message,
            model=model,
            temperature=temperature
        ):
            yield {
                "type": "answer",
                "content": chunk,
                "done": False
            }
        
        # Signal completion
        yield {
            "type": "answer",
            "content": "",
            "done": True
        }
        
        logger.info("Streaming answer generation completed")
        
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
