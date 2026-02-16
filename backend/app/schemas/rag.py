"""
Pydantic schemas for RAG (Retrieval-Augmented Generation) endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class RAGQueryRequest(BaseModel):
    """Request schema for RAG question answering."""
    
    query: str = Field(
        ...,
        description="The question to ask about policy documents",
        min_length=1,
        max_length=1000,
        examples=["What are the eligibility criteria for this program?"]
    )
    
    policy_id: Optional[str] = Field(
        None,
        description="Optional policy ID to limit search scope. If not provided, searches across all policies.",
        examples=["pol_abc123"]
    )
    
    top_k: int = Field(
        5,
        description="Number of relevant document chunks to retrieve",
        ge=1,
        le=20
    )
    
    temperature: Optional[float] = Field(
        None,
        description="LLM sampling temperature (0.0-2.0). Lower is more focused, higher is more creative.",
        ge=0.0,
        le=2.0
    )
    
    model: Optional[str] = Field(
        None,
        description="LLM model to use. If not provided, uses default from config.",
        examples=["gpt-4-turbo-preview", "gpt-3.5-turbo"]
    )
    
    language: Optional[str] = Field(
        None,
        description="Language code for the response (e.g., 'en', 'es', 'fr'). If not provided, auto-detects from query.",
        examples=["en", "es", "fr", "hi", "zh-cn"]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the income requirements for this housing program?",
                "policy_id": "pol_abc123",
                "top_k": 5,
                "temperature": 0.7,
                "language": "en"
            }
        }


class SourceChunk(BaseModel):
    """Source chunk with metadata."""
    
    chunk_id: int = Field(..., description="Database ID of the chunk")
    chunk_text: str = Field(..., description="Text content of the chunk")
    chunk_index: int = Field(..., description="Index of chunk within the policy")
    policy_id: str = Field(..., description="Policy identifier")
    policy_title: Optional[str] = Field(None, description="Title of the policy document")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    start_char: int = Field(..., description="Starting character position in original document")
    end_char: int = Field(..., description="Ending character position in original document")


class EvaluationMetrics(BaseModel):
    """Evaluation metrics for AI-generated outputs."""
    
    relevance_score: float = Field(..., description="How relevant the answer is to the query (0-1)")
    coherence_score: float = Field(..., description="Coherence and readability of the answer (0-1)")
    completeness_score: float = Field(..., description="Whether the answer provides sufficient detail (0-1)")
    source_grounding_score: float = Field(..., description="How well claims are supported by sources (0-1)")
    hallucination_risk: str = Field(..., description="Risk of hallucination: low, medium, or high")
    citation_quality: float = Field(..., description="Quality of source citations (0-1)")
    safety_score: float = Field(..., description="Safety score, 1.0 = safe (0-1)")
    bias_indicators: List[str] = Field(..., description="List of potential bias indicators detected")
    quality_flags: List[str] = Field(..., description="List of quality issues detected")
    overall_confidence: float = Field(..., description="Overall confidence in the response (0-1)")


class RAGResponse(BaseModel):
    """Response schema for RAG question answering."""
    
    answer: str = Field(..., description="Generated answer to the question")
    sources: List[SourceChunk] = Field(..., description="Source chunks used to generate the answer")
    query: str = Field(..., description="Original query")
    model_used: str = Field(..., description="LLM model used for generation")
    timestamp: str = Field(..., description="ISO timestamp of when the answer was generated")
    num_sources: int = Field(..., description="Number of source chunks used")
    detected_language: str = Field(..., description="Detected language code from the query")
    response_language: str = Field(..., description="Language code of the response")
    evaluation: Optional[EvaluationMetrics] = Field(None, description="Evaluation metrics for the generated answer")
    cached: Optional[bool] = Field(None, description="Whether this response was served from cache")

    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The income requirements for this housing program are...",
                "sources": [
                    {
                        "chunk_id": 123,
                        "chunk_text": "Eligibility criteria include...",
                        "chunk_index": 5,
                        "policy_id": "pol_abc123",
                        "policy_title": "Affordable Housing Policy 2024",
                        "similarity_score": 0.89,
                        "start_char": 1500,
                        "end_char": 2000
                    }
                ],
                "query": "What are the income requirements for this housing program?",
                "model_used": "gpt-4-turbo-preview",
                "timestamp": "2026-02-11T22:23:46Z",
                "num_sources": 3,
                "detected_language": "en",
                "response_language": "en",
                "evaluation": {
                    "relevance_score": 0.92,
                    "coherence_score": 0.88,
                    "completeness_score": 0.85,
                    "source_grounding_score": 0.91,
                    "hallucination_risk": "low",
                    "citation_quality": 0.80,
                    "safety_score": 1.0,
                    "bias_indicators": [],
                    "quality_flags": [],
                    "overall_confidence": 0.89
                },
                "cached": False
            }
        }


class RAGStreamChunk(BaseModel):
    """Streaming response chunk for RAG."""
    
    type: str = Field(..., description="Type of chunk: 'sources', 'answer', or 'evaluation'")
    content: Optional[str] = Field(None, description="Content chunk (for answer type)")
    sources: Optional[List[SourceChunk]] = Field(None, description="Source chunks (for sources type)")
    num_sources: Optional[int] = Field(None, description="Number of sources (for sources type)")
    done: Optional[bool] = Field(None, description="Whether streaming is complete (for answer type)")
    evaluation: Optional[EvaluationMetrics] = Field(None, description="Evaluation metrics (for evaluation type)")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "type": "sources",
                    "sources": [...],
                    "num_sources": 3
                },
                {
                    "type": "answer",
                    "content": "The income requirements",
                    "done": False
                },
                {
                    "type": "answer",
                    "content": "",
                    "done": True
                },
                {
                    "type": "evaluation",
                    "evaluation": {
                        "relevance_score": 0.95,
                        "coherence_score": 0.90,
                        # ... other metrics
                    }
                }
            ]
        }
