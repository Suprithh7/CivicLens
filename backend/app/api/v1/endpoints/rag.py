"""
RAG (Retrieval-Augmented Generation) API endpoints.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_db
from app.schemas.rag import RAGQueryRequest, RAGResponse, RAGStreamChunk
from app.services.rag_service import (
    answer_question,
    answer_question_streaming,
    RAGError
)
from app.services.llm_service import LLMError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/ask",
    response_model=RAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question about policy documents",
    description="Use RAG to answer questions based on policy document content. "
                "Retrieves relevant chunks and generates an answer using an LLM."
)
async def ask_question(
    request: RAGQueryRequest,
    db: AsyncSession = Depends(get_db)
) -> RAGResponse:
    """
    Answer a question using the RAG pipeline.
    
    This endpoint:
    1. Retrieves relevant document chunks using semantic search
    2. Constructs a prompt with the retrieved context
    3. Generates an answer using an LLM
    4. Returns the answer with source citations
    
    Args:
        request: RAG query request with question and parameters
        db: Database session
        
    Returns:
        RAG response with answer and sources
        
    Raises:
        HTTPException: If RAG pipeline fails
    """
    try:
        logger.info(f"Received RAG query: '{request.query}'")
        
        response = await answer_question(
            query=request.query,
            db=db,
            policy_id=request.policy_id,
            top_k=request.top_k,
            model=request.model,
            temperature=request.temperature
        )
        
        return RAGResponse(**response)
        
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
    except RAGError as e:
        logger.error(f"RAG error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "RAG pipeline error",
                "error": str(e),
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in ask endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to process question",
                "error": str(e)
            }
        )


@router.post(
    "/ask-stream",
    status_code=status.HTTP_200_OK,
    summary="Ask a question with streaming response",
    description="Use RAG to answer questions with a streaming response. "
                "Returns sources first, then streams the answer as it's generated."
)
async def ask_question_stream(
    request: RAGQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Answer a question using the RAG pipeline with streaming response.
    
    This endpoint:
    1. Retrieves relevant document chunks using semantic search
    2. Returns sources immediately
    3. Streams the generated answer in real-time
    
    The response is a stream of JSON objects with the following format:
    - First chunk: {"type": "sources", "sources": [...], "num_sources": N}
    - Answer chunks: {"type": "answer", "content": "...", "done": false}
    - Final chunk: {"type": "answer", "content": "", "done": true}
    
    Args:
        request: RAG query request with question and parameters
        db: Database session
        
    Returns:
        Streaming response with answer chunks
        
    Raises:
        HTTPException: If RAG pipeline fails
    """
    async def generate():
        try:
            logger.info(f"Received streaming RAG query: '{request.query}'")
            
            async for chunk in answer_question_streaming(
                query=request.query,
                db=db,
                policy_id=request.policy_id,
                top_k=request.top_k,
                model=request.model,
                temperature=request.temperature
            ):
                # Convert chunk to JSON and send with newline delimiter
                yield json.dumps(chunk) + "\n"
                
        except LLMError as e:
            logger.error(f"LLM error in streaming: {e}")
            error_chunk = {
                "type": "error",
                "error": "LLM service error",
                "details": str(e)
            }
            yield json.dumps(error_chunk) + "\n"
            
        except RAGError as e:
            logger.error(f"RAG error in streaming: {e}")
            error_chunk = {
                "type": "error",
                "error": "RAG pipeline error",
                "details": str(e)
            }
            yield json.dumps(error_chunk) + "\n"
            
        except Exception as e:
            logger.error(f"Unexpected error in streaming: {e}")
            error_chunk = {
                "type": "error",
                "error": "Failed to process question",
                "details": str(e)
            }
            yield json.dumps(error_chunk) + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Check RAG service health",
    description="Check if the RAG service and LLM are properly configured"
)
async def health_check():
    """
    Check RAG service health.
    
    Returns:
        Health status information
    """
    from app.config import settings
    
    health_status = {
        "status": "healthy",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "api_key_configured": bool(settings.LLM_API_KEY)
    }
    
    if not settings.LLM_API_KEY:
        health_status["status"] = "degraded"
        health_status["warning"] = "LLM API key not configured"
    
    return health_status
