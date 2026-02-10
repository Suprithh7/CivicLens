"""
Semantic search service using FAISS vector similarity.
"""

import logging
from typing import List, Dict, Optional
import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.policy import Policy, PolicyChunk
from app.services.faiss_service import FAISSIndexManager, FAISSError
from app.services.embedding_service import generate_embedding
from app.core.exceptions import CivicLensException

logger = logging.getLogger(__name__)


class SearchError(CivicLensException):
    """Exception raised when search operations fail."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details or {}
        )


async def semantic_search_policy(
    policy_id: str,
    query: str,
    db: AsyncSession,
    top_k: int = 5
) -> List[Dict]:
    """
    Perform semantic search within a specific policy.
    
    Args:
        policy_id: Unique policy identifier
        query: Natural language search query
        db: Database session
        top_k: Number of results to return
        
    Returns:
        List of search results with chunks and scores
        
    Raises:
        SearchError: If search fails
    """
    try:
        logger.info(f"Searching policy {policy_id} with query: {query}")
        
        # Get policy
        stmt = select(Policy).where(
            Policy.policy_id == policy_id,
            Policy.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise SearchError(
                f"Policy not found: {policy_id}",
                details={"policy_id": policy_id}
            )
        
        # Generate query embedding
        query_embedding = generate_embedding(query)
        query_vector = np.array(query_embedding, dtype='float32')
        
        # Search FAISS index
        manager = FAISSIndexManager()
        chunk_ids, distances = manager.search(policy_id, query_vector, top_k)
        
        # Fetch chunks from database
        chunks_stmt = select(PolicyChunk).where(
            PolicyChunk.id.in_(chunk_ids)
        )
        chunks_result = await db.execute(chunks_stmt)
        chunks_dict = {chunk.id: chunk for chunk in chunks_result.scalars().all()}
        
        # Build results maintaining order from FAISS
        results = []
        for chunk_id, distance in zip(chunk_ids, distances):
            if chunk_id in chunks_dict:
                chunk = chunks_dict[chunk_id]
                # Convert L2 distance to similarity score (0-1, higher is better)
                # Using exponential decay: score = exp(-distance)
                similarity_score = float(np.exp(-distance))
                
                results.append({
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.chunk_text,
                    "similarity_score": similarity_score,
                    "distance": float(distance),
                    "policy_id": policy_id,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "metadata": chunk.metadata_json
                })
        
        logger.info(f"Found {len(results)} results for query in policy {policy_id}")
        
        return results
        
    except (SearchError, FAISSError):
        raise
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise SearchError(
            f"Search failed: {str(e)}",
            details={"policy_id": policy_id, "query": query}
        )


async def semantic_search_all(
    query: str,
    db: AsyncSession,
    top_k: int = 10,
    policy_ids: Optional[List[str]] = None
) -> List[Dict]:
    """
    Perform semantic search across all policies or a subset.
    
    Args:
        query: Natural language search query
        db: Database session
        top_k: Total number of results to return
        policy_ids: Optional list of policy IDs to search within
        
    Returns:
        List of search results with chunks and scores
        
    Raises:
        SearchError: If search fails
    """
    try:
        logger.info(f"Searching all policies with query: {query}")
        
        # Get policies
        stmt = select(Policy).where(Policy.deleted_at.is_(None))
        if policy_ids:
            stmt = stmt.where(Policy.policy_id.in_(policy_ids))
        
        result = await db.execute(stmt)
        policies = result.scalars().all()
        
        if not policies:
            return []
        
        # Generate query embedding once
        query_embedding = generate_embedding(query)
        query_vector = np.array(query_embedding, dtype='float32')
        
        # Search each policy's index
        all_results = []
        manager = FAISSIndexManager()
        
        for policy in policies:
            try:
                # Try to search this policy
                chunk_ids, distances = manager.search(
                    policy.policy_id,
                    query_vector,
                    top_k=top_k  # Get top_k from each policy
                )
                
                # Fetch chunks
                chunks_stmt = select(PolicyChunk).where(
                    PolicyChunk.id.in_(chunk_ids)
                )
                chunks_result = await db.execute(chunks_stmt)
                chunks_dict = {chunk.id: chunk for chunk in chunks_result.scalars().all()}
                
                # Add results
                for chunk_id, distance in zip(chunk_ids, distances):
                    if chunk_id in chunks_dict:
                        chunk = chunks_dict[chunk_id]
                        similarity_score = float(np.exp(-distance))
                        
                        all_results.append({
                            "chunk_id": chunk.id,
                            "chunk_index": chunk.chunk_index,
                            "chunk_text": chunk.chunk_text,
                            "similarity_score": similarity_score,
                            "distance": float(distance),
                            "policy_id": policy.policy_id,
                            "policy_title": policy.title,
                            "start_char": chunk.start_char,
                            "end_char": chunk.end_char,
                            "metadata": chunk.metadata_json
                        })
                
            except FAISSError as e:
                # Skip policies without indices
                logger.warning(f"Skipping policy {policy.policy_id}: {str(e)}")
                continue
        
        # Sort all results by similarity score (descending)
        all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Return top_k results
        results = all_results[:top_k]
        
        logger.info(f"Found {len(results)} results across {len(policies)} policies")
        
        return results
        
    except SearchError:
        raise
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise SearchError(
            f"Search failed: {str(e)}",
            details={"query": query}
        )


async def find_similar_chunks(
    policy_id: str,
    chunk_index: int,
    db: AsyncSession,
    top_k: int = 5
) -> List[Dict]:
    """
    Find chunks similar to a given chunk.
    
    Args:
        policy_id: Unique policy identifier
        chunk_index: Index of the reference chunk
        db: Database session
        top_k: Number of similar chunks to return
        
    Returns:
        List of similar chunks with scores
        
    Raises:
        SearchError: If search fails
    """
    try:
        logger.info(f"Finding similar chunks to {policy_id}:{chunk_index}")
        
        # Get policy
        stmt = select(Policy).where(
            Policy.policy_id == policy_id,
            Policy.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise SearchError(
                f"Policy not found: {policy_id}",
                details={"policy_id": policy_id}
            )
        
        # Get reference chunk
        chunk_stmt = select(PolicyChunk).where(
            PolicyChunk.policy_id == policy.id,
            PolicyChunk.chunk_index == chunk_index
        )
        chunk_result = await db.execute(chunk_stmt)
        reference_chunk = chunk_result.scalar_one_or_none()
        
        if not reference_chunk:
            raise SearchError(
                f"Chunk not found: {chunk_index}",
                details={"policy_id": policy_id, "chunk_index": chunk_index}
            )
        
        if not reference_chunk.embedding:
            raise SearchError(
                "Reference chunk has no embedding",
                details={"policy_id": policy_id, "chunk_index": chunk_index}
            )
        
        # Use chunk's embedding as query
        query_vector = np.array(reference_chunk.embedding, dtype='float32')
        
        # Search FAISS index (get top_k + 1 to exclude self)
        manager = FAISSIndexManager()
        chunk_ids, distances = manager.search(policy_id, query_vector, top_k + 1)
        
        # Fetch chunks
        chunks_stmt = select(PolicyChunk).where(
            PolicyChunk.id.in_(chunk_ids)
        )
        chunks_result = await db.execute(chunks_stmt)
        chunks_dict = {chunk.id: chunk for chunk in chunks_result.scalars().all()}
        
        # Build results, excluding the reference chunk itself
        results = []
        for chunk_id, distance in zip(chunk_ids, distances):
            if chunk_id in chunks_dict and chunk_id != reference_chunk.id:
                chunk = chunks_dict[chunk_id]
                similarity_score = float(np.exp(-distance))
                
                results.append({
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.chunk_text,
                    "similarity_score": similarity_score,
                    "distance": float(distance),
                    "policy_id": policy_id,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "metadata": chunk.metadata_json
                })
                
                if len(results) >= top_k:
                    break
        
        logger.info(f"Found {len(results)} similar chunks")
        
        return results
        
    except SearchError:
        raise
    except Exception as e:
        logger.error(f"Finding similar chunks failed: {str(e)}", exc_info=True)
        raise SearchError(
            f"Finding similar chunks failed: {str(e)}",
            details={"policy_id": policy_id, "chunk_index": chunk_index}
        )
