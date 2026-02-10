"""
Pydantic schemas for text chunks.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChunkBase(BaseModel):
    """Base schema for chunk data."""
    chunk_index: int = Field(..., ge=0, description="Sequential index of chunk (0-based)")
    chunk_text: str = Field(..., min_length=1, description="Text content of the chunk")
    chunk_size: int = Field(..., gt=0, description="Size of chunk in characters")


class ChunkCreate(ChunkBase):
    """Schema for creating a chunk."""
    start_char: int = Field(..., ge=0, description="Starting character position in original document")
    end_char: int = Field(..., gt=0, description="Ending character position in original document")
    page_numbers: Optional[List[int]] = Field(None, description="Page numbers this chunk spans")
    metadata_json: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChunkPublic(ChunkBase):
    """Public-facing chunk schema with all metadata."""
    id: int
    policy_id: int
    start_char: int
    end_char: int
    page_numbers: Optional[List[int]] = None
    metadata_json: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = Field(None, description="Vector embedding for semantic search")
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ChunkSummary(BaseModel):
    """Summary information about a chunk (without full text)."""
    id: int
    chunk_index: int
    chunk_size: int
    start_char: int
    end_char: int
    text_preview: str = Field(..., description="First 100 characters of chunk")
    
    model_config = ConfigDict(from_attributes=True)


class ChunkListResponse(BaseModel):
    """Response for paginated chunk list."""
    chunks: List[ChunkPublic]
    total: int = Field(..., description="Total number of chunks for this policy")
    limit: int
    offset: int
    policy_id: str


class ChunkingRequest(BaseModel):
    """Request parameters for chunking operation."""
    chunk_size: int = Field(1000, ge=100, le=5000, description="Target chunk size in characters")
    overlap: int = Field(200, ge=0, le=500, description="Overlap between chunks in characters")
    force: bool = Field(False, description="Force re-chunking even if already chunked")


class ChunkingResponse(BaseModel):
    """Response for chunking operation."""
    policy_id: str
    processing_id: int
    status: str
    chunk_count: int
    chunk_size_config: int
    overlap_config: int
    avg_chunk_size: int
    min_chunk_size: int
    max_chunk_size: int
    total_characters: int
    chunking_timestamp: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "policy_id": "pol_abc123xyz",
                "processing_id": 42,
                "status": "completed",
                "chunk_count": 15,
                "chunk_size_config": 1000,
                "overlap_config": 200,
                "avg_chunk_size": 987,
                "min_chunk_size": 456,
                "max_chunk_size": 1200,
                "total_characters": 14805,
                "chunking_timestamp": "2026-02-09T22:37:00.000000"
            }
        }
    )


class EmbeddingRequest(BaseModel):
    """Request parameters for embedding generation."""
    force: bool = Field(False, description="Force regeneration even if embeddings exist")
    batch_size: int = Field(32, ge=1, le=128, description="Number of chunks to process per batch")


class EmbeddingResponse(BaseModel):
    """Response for embedding generation operation."""
    policy_id: str
    processing_id: int
    status: str
    chunk_count: int
    embedding_dimension: int
    model_name: str
    embedding_timestamp: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "policy_id": "pol_abc123xyz",
                "processing_id": 43,
                "status": "completed",
                "chunk_count": 15,
                "embedding_dimension": 384,
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "embedding_timestamp": "2026-02-10T22:58:00.000000"
            }
        }
    )


class EmbeddingStatusResponse(BaseModel):
    """Response for embedding status check."""
    policy_id: str
    processing_id: Optional[int] = None
    status: str
    progress_percent: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
