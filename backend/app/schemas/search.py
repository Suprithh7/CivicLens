"""
Pydantic schemas for semantic search.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any


class SearchRequest(BaseModel):
    """Request parameters for semantic search."""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language search query")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to return")
    policy_ids: Optional[List[str]] = Field(None, description="Optional list of policy IDs to search within")


class SearchResult(BaseModel):
    """Individual search result."""
    chunk_id: int
    chunk_index: int
    chunk_text: str
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity score (0-1, higher is better)")
    distance: float = Field(..., description="L2 distance from query")
    policy_id: str
    policy_title: Optional[str] = None
    start_char: int
    end_char: int
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    """Response for search operation."""
    query: str
    results: List[SearchResult]
    total_results: int
    search_type: str = Field(..., description="Type of search: 'policy' or 'all'")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "healthcare benefits for rural areas",
                "results": [
                    {
                        "chunk_id": 123,
                        "chunk_index": 5,
                        "chunk_text": "Rural healthcare benefits include...",
                        "similarity_score": 0.89,
                        "distance": 0.12,
                        "policy_id": "pol_abc123xyz",
                        "policy_title": "Rural Healthcare Policy 2024",
                        "start_char": 5000,
                        "end_char": 6000,
                        "metadata": {"sentence_count": 8}
                    }
                ],
                "total_results": 1,
                "search_type": "all"
            }
        }
    )


class SimilarChunksRequest(BaseModel):
    """Request parameters for finding similar chunks."""
    top_k: int = Field(5, ge=1, le=20, description="Number of similar chunks to return")


class SimilarChunksResponse(BaseModel):
    """Response for similar chunks operation."""
    reference_chunk_index: int
    policy_id: str
    results: List[SearchResult]
    total_results: int
