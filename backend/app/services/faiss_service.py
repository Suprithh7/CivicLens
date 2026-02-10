"""
FAISS index management service for vector similarity search.
Handles creation, persistence, and querying of FAISS indices.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import faiss

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.policy import Policy, PolicyChunk
from app.core.exceptions import CivicLensException

logger = logging.getLogger(__name__)

# FAISS index storage directory
FAISS_INDEX_DIR = Path(__file__).parent.parent.parent / "faiss_indices"
FAISS_INDEX_DIR.mkdir(exist_ok=True)


class FAISSError(CivicLensException):
    """Exception raised when FAISS operations fail."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details or {}
        )


class FAISSIndexManager:
    """Manages FAISS indices for policy chunks."""
    
    def __init__(self, dimension: int = 384):
        """
        Initialize FAISS index manager.
        
        Args:
            dimension: Embedding vector dimension
        """
        self.dimension = dimension
        self.indices: Dict[str, faiss.Index] = {}  # policy_id -> index
        self.id_maps: Dict[str, List[int]] = {}  # policy_id -> chunk_ids
    
    def _get_index_path(self, policy_id: str) -> Path:
        """Get the file path for a policy's FAISS index."""
        return FAISS_INDEX_DIR / f"{policy_id}.index"
    
    def _get_id_map_path(self, policy_id: str) -> Path:
        """Get the file path for a policy's ID mapping."""
        return FAISS_INDEX_DIR / f"{policy_id}_ids.npy"
    
    def build_index(
        self,
        policy_id: str,
        embeddings: np.ndarray,
        chunk_ids: List[int]
    ) -> faiss.Index:
        """
        Build a FAISS index from embeddings.
        
        Args:
            policy_id: Unique policy identifier
            embeddings: Numpy array of embeddings (n_vectors, dimension)
            chunk_ids: List of chunk IDs corresponding to embeddings
            
        Returns:
            FAISS index
            
        Raises:
            FAISSError: If index building fails
        """
        try:
            if embeddings.shape[0] != len(chunk_ids):
                raise FAISSError(
                    "Number of embeddings must match number of chunk IDs",
                    details={
                        "embeddings_count": embeddings.shape[0],
                        "chunk_ids_count": len(chunk_ids)
                    }
                )
            
            if embeddings.shape[1] != self.dimension:
                raise FAISSError(
                    f"Embedding dimension mismatch. Expected {self.dimension}, got {embeddings.shape[1]}",
                    details={"expected": self.dimension, "actual": embeddings.shape[1]}
                )
            
            logger.info(f"Building FAISS index for policy {policy_id} with {len(chunk_ids)} vectors")
            
            # Create a flat L2 index for exact search
            index = faiss.IndexFlatL2(self.dimension)
            
            # Ensure embeddings are float32 and C-contiguous
            embeddings = np.ascontiguousarray(embeddings.astype('float32'))
            
            # Add vectors to index
            index.add(embeddings)
            
            # Store in memory
            self.indices[policy_id] = index
            self.id_maps[policy_id] = chunk_ids
            
            logger.info(f"FAISS index built successfully for policy {policy_id}")
            
            return index
            
        except FAISSError:
            raise
        except Exception as e:
            logger.error(f"Failed to build FAISS index: {str(e)}", exc_info=True)
            raise FAISSError(
                f"Failed to build FAISS index: {str(e)}",
                details={"policy_id": policy_id}
            )
    
    def save_index(self, policy_id: str) -> None:
        """
        Save FAISS index to disk.
        
        Args:
            policy_id: Unique policy identifier
            
        Raises:
            FAISSError: If saving fails
        """
        try:
            if policy_id not in self.indices:
                raise FAISSError(
                    f"No index found for policy {policy_id}",
                    details={"policy_id": policy_id}
                )
            
            index_path = self._get_index_path(policy_id)
            id_map_path = self._get_id_map_path(policy_id)
            
            # Save FAISS index
            faiss.write_index(self.indices[policy_id], str(index_path))
            
            # Save ID mapping
            np.save(str(id_map_path), np.array(self.id_maps[policy_id]))
            
            logger.info(f"Saved FAISS index for policy {policy_id} to {index_path}")
            
        except FAISSError:
            raise
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {str(e)}", exc_info=True)
            raise FAISSError(
                f"Failed to save FAISS index: {str(e)}",
                details={"policy_id": policy_id}
            )
    
    def load_index(self, policy_id: str) -> faiss.Index:
        """
        Load FAISS index from disk.
        
        Args:
            policy_id: Unique policy identifier
            
        Returns:
            FAISS index
            
        Raises:
            FAISSError: If loading fails
        """
        try:
            # Check if already loaded
            if policy_id in self.indices:
                return self.indices[policy_id]
            
            index_path = self._get_index_path(policy_id)
            id_map_path = self._get_id_map_path(policy_id)
            
            if not index_path.exists():
                raise FAISSError(
                    f"Index file not found for policy {policy_id}",
                    details={"policy_id": policy_id, "path": str(index_path)}
                )
            
            # Load FAISS index
            index = faiss.read_index(str(index_path))
            
            # Load ID mapping
            chunk_ids = np.load(str(id_map_path)).tolist()
            
            # Store in memory
            self.indices[policy_id] = index
            self.id_maps[policy_id] = chunk_ids
            
            logger.info(f"Loaded FAISS index for policy {policy_id} from {index_path}")
            
            return index
            
        except FAISSError:
            raise
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {str(e)}", exc_info=True)
            raise FAISSError(
                f"Failed to load FAISS index: {str(e)}",
                details={"policy_id": policy_id}
            )
    
    def search(
        self,
        policy_id: str,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> Tuple[List[int], List[float]]:
        """
        Search for similar vectors in the index.
        
        Args:
            policy_id: Unique policy identifier
            query_embedding: Query vector (1D array of dimension)
            top_k: Number of nearest neighbors to return
            
        Returns:
            Tuple of (chunk_ids, distances)
            
        Raises:
            FAISSError: If search fails
        """
        try:
            # Load index if not in memory
            if policy_id not in self.indices:
                self.load_index(policy_id)
            
            index = self.indices[policy_id]
            chunk_ids = self.id_maps[policy_id]
            
            # Ensure query is 2D and float32
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            query_embedding = np.ascontiguousarray(query_embedding.astype('float32'))
            
            # Perform search
            distances, indices = index.search(query_embedding, min(top_k, index.ntotal))
            
            # Map indices to chunk IDs
            result_chunk_ids = [chunk_ids[idx] for idx in indices[0]]
            result_distances = distances[0].tolist()
            
            logger.info(f"Search completed for policy {policy_id}, found {len(result_chunk_ids)} results")
            
            return result_chunk_ids, result_distances
            
        except FAISSError:
            raise
        except Exception as e:
            logger.error(f"Failed to search FAISS index: {str(e)}", exc_info=True)
            raise FAISSError(
                f"Failed to search FAISS index: {str(e)}",
                details={"policy_id": policy_id}
            )
    
    def delete_index(self, policy_id: str) -> None:
        """
        Delete FAISS index from memory and disk.
        
        Args:
            policy_id: Unique policy identifier
        """
        try:
            # Remove from memory
            if policy_id in self.indices:
                del self.indices[policy_id]
            if policy_id in self.id_maps:
                del self.id_maps[policy_id]
            
            # Remove from disk
            index_path = self._get_index_path(policy_id)
            id_map_path = self._get_id_map_path(policy_id)
            
            if index_path.exists():
                index_path.unlink()
            if id_map_path.exists():
                id_map_path.unlink()
            
            logger.info(f"Deleted FAISS index for policy {policy_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete FAISS index: {str(e)}", exc_info=True)
            raise FAISSError(
                f"Failed to delete FAISS index: {str(e)}",
                details={"policy_id": policy_id}
            )


async def build_policy_index(policy_id: str, db: AsyncSession) -> Dict:
    """
    Build FAISS index for a policy from its chunk embeddings.
    
    Args:
        policy_id: Unique policy identifier
        db: Database session
        
    Returns:
        dict: Index building result
        
    Raises:
        FAISSError: If index building fails
    """
    logger.info(f"Building FAISS index for policy: {policy_id}")
    
    # Get policy
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise FAISSError(
            f"Policy not found: {policy_id}",
            details={"policy_id": policy_id}
        )
    
    # Get chunks with embeddings
    chunks_stmt = select(PolicyChunk).where(
        PolicyChunk.policy_id == policy.id,
        PolicyChunk.embedding.isnot(None)
    ).order_by(PolicyChunk.chunk_index)
    
    chunks_result = await db.execute(chunks_stmt)
    chunks = chunks_result.scalars().all()
    
    if not chunks:
        raise FAISSError(
            "No chunks with embeddings found. Please generate embeddings first.",
            details={"policy_id": policy_id}
        )
    
    # Extract embeddings and IDs
    embeddings = np.array([chunk.embedding for chunk in chunks], dtype='float32')
    chunk_ids = [chunk.id for chunk in chunks]
    
    # Build index
    manager = FAISSIndexManager()
    manager.build_index(policy_id, embeddings, chunk_ids)
    
    # Save to disk
    manager.save_index(policy_id)
    
    return {
        "policy_id": policy_id,
        "status": "completed",
        "vector_count": len(chunk_ids),
        "index_path": str(manager._get_index_path(policy_id))
    }
