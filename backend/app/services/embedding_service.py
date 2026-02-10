"""
Embedding service for generating vector embeddings from text.
Uses sentence-transformers to create semantic embeddings for policy chunks.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sentence_transformers import SentenceTransformer

from app.models.policy import Policy, PolicyChunk, PolicyProcessing, ProcessingStage, ProcessingStatus
from app.core.exceptions import CivicLensException

logger = logging.getLogger(__name__)

# Default embedding model
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2


class EmbeddingError(CivicLensException):
    """Exception raised when embedding generation fails."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details or {}
        )


class EmbeddingModel:
    """Singleton wrapper for sentence-transformers model."""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
        return cls._instance
    
    def load_model(self, model_name: str = DEFAULT_MODEL):
        """Load the sentence-transformers model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {model_name}")
            try:
                self._model = SentenceTransformer(model_name)
                logger.info(f"Model loaded successfully. Embedding dimension: {self._model.get_sentence_embedding_dimension()}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {str(e)}", exc_info=True)
                raise EmbeddingError(
                    f"Failed to load embedding model: {str(e)}",
                    details={"model_name": model_name}
                )
        return self._model
    
    def get_model(self):
        """Get the loaded model, loading it if necessary."""
        if self._model is None:
            return self.load_model()
        return self._model


def generate_embedding(text: str, model_name: str = DEFAULT_MODEL) -> List[float]:
    """
    Generate embedding for a single text.
    
    Args:
        text: Input text to embed
        model_name: Name of the sentence-transformers model to use
        
    Returns:
        List of floats representing the embedding vector
        
    Raises:
        EmbeddingError: If embedding generation fails
    """
    try:
        if not text or not text.strip():
            raise EmbeddingError("Cannot generate embedding for empty text")
        
        # Get or load model
        embedding_model = EmbeddingModel()
        model = embedding_model.get_model()
        
        # Generate embedding
        embedding = model.encode(text, convert_to_numpy=True)
        
        # Convert to list and return
        return embedding.tolist()
        
    except EmbeddingError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during embedding generation: {str(e)}", exc_info=True)
        raise EmbeddingError(
            f"Failed to generate embedding: {str(e)}",
            details={"text_length": len(text) if text else 0}
        )


def generate_embeddings_batch(
    texts: List[str], 
    model_name: str = DEFAULT_MODEL,
    batch_size: int = 32
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batch.
    
    Args:
        texts: List of input texts to embed
        model_name: Name of the sentence-transformers model to use
        batch_size: Number of texts to process in each batch
        
    Returns:
        List of embedding vectors
        
    Raises:
        EmbeddingError: If embedding generation fails
    """
    try:
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise EmbeddingError("Cannot generate embeddings for empty texts")
        
        logger.info(f"Generating embeddings for {len(valid_texts)} texts in batches of {batch_size}")
        
        # Get or load model
        embedding_model = EmbeddingModel()
        model = embedding_model.get_model()
        
        # Generate embeddings in batch
        embeddings = model.encode(
            valid_texts, 
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(valid_texts) > 100
        )
        
        # Convert to list of lists
        return [emb.tolist() for emb in embeddings]
        
    except EmbeddingError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during batch embedding generation: {str(e)}", exc_info=True)
        raise EmbeddingError(
            f"Failed to generate batch embeddings: {str(e)}",
            details={"text_count": len(texts)}
        )


async def process_policy_embeddings(
    policy_id: str,
    db: AsyncSession,
    force: bool = False,
    batch_size: int = 32
) -> Dict:
    """
    Generate embeddings for all chunks of a policy document.
    
    Args:
        policy_id: Unique policy identifier
        db: Database session
        force: If True, regenerate embeddings even if they exist
        batch_size: Number of chunks to process in each batch
        
    Returns:
        dict: Embedding generation result with statistics
        
    Raises:
        EmbeddingError: If embedding generation fails
    """
    logger.info(f"Processing embeddings for policy: {policy_id}")
    
    # Get policy from database
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise EmbeddingError(
            f"Policy not found: {policy_id}",
            details={"policy_id": policy_id}
        )
    
    # Check if chunks exist
    chunks_stmt = select(PolicyChunk).where(
        PolicyChunk.policy_id == policy.id
    ).order_by(PolicyChunk.chunk_index)
    chunks_result = await db.execute(chunks_stmt)
    chunks = chunks_result.scalars().all()
    
    if not chunks:
        raise EmbeddingError(
            "Cannot generate embeddings: no chunks found. Please chunk the policy first.",
            details={"policy_id": policy_id}
        )
    
    # Check for existing embedding processing record
    embed_proc_stmt = select(PolicyProcessing).where(
        PolicyProcessing.policy_id == policy.id,
        PolicyProcessing.stage == ProcessingStage.EMBEDDING
    )
    embed_proc_result = await db.execute(embed_proc_stmt)
    processing_record = embed_proc_result.scalar_one_or_none()
    
    # Check if already processed (unless force=True)
    if processing_record and not force:
        if processing_record.status == ProcessingStatus.COMPLETED:
            raise EmbeddingError(
                "Embeddings have already been generated. Use force=true to regenerate.",
                details={"policy_id": policy_id, "processing_id": processing_record.id}
            )
        elif processing_record.status == ProcessingStatus.IN_PROGRESS:
            raise EmbeddingError(
                "Embedding generation is already in progress",
                details={"policy_id": policy_id, "processing_id": processing_record.id}
            )
    
    # Create or update processing record
    if not processing_record:
        processing_record = PolicyProcessing(
            policy_id=policy.id,
            stage=ProcessingStage.EMBEDDING,
            status=ProcessingStatus.IN_PROGRESS,
            progress_percent=0,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(processing_record)
    else:
        # Reset for regeneration
        processing_record.status = ProcessingStatus.IN_PROGRESS
        processing_record.progress_percent = 0
        processing_record.started_at = datetime.utcnow()
        processing_record.error_message = None
        processing_record.result_data = None
    
    await db.commit()
    await db.refresh(processing_record)
    
    try:
        # Extract chunk texts
        chunk_texts = [chunk.chunk_text for chunk in chunks]
        
        logger.info(f"Generating embeddings for {len(chunk_texts)} chunks")
        
        # Generate embeddings in batch
        embeddings = generate_embeddings_batch(chunk_texts, batch_size=batch_size)
        
        # Update chunks with embeddings
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        await db.commit()
        
        # Calculate statistics
        result_data = {
            "chunk_count": len(chunks),
            "embedding_dimension": len(embeddings[0]) if embeddings else 0,
            "model_name": DEFAULT_MODEL,
            "embedding_timestamp": datetime.utcnow().isoformat()
        }
        
        # Update processing record
        processing_record.status = ProcessingStatus.COMPLETED
        processing_record.progress_percent = 100
        processing_record.completed_at = datetime.utcnow()
        processing_record.result_data = result_data
        
        await db.commit()
        await db.refresh(processing_record)
        
        logger.info(f"Embedding generation completed for policy: {policy_id}, processed {len(chunks)} chunks")
        
        return {
            "policy_id": policy_id,
            "processing_id": processing_record.id,
            "status": "completed",
            **result_data
        }
        
    except Exception as e:
        # Update processing record with error
        processing_record.status = ProcessingStatus.FAILED
        processing_record.error_message = str(e)
        processing_record.completed_at = datetime.utcnow()
        
        await db.commit()
        
        logger.error(f"Embedding generation failed for policy {policy_id}: {str(e)}", exc_info=True)
        
        raise EmbeddingError(
            f"Embedding generation failed: {str(e)}",
            details={"policy_id": policy_id, "processing_id": processing_record.id}
        )


async def get_embedding_status(policy_id: str, db: AsyncSession) -> Dict:
    """
    Get the status of embedding generation for a policy.
    
    Args:
        policy_id: Unique policy identifier
        db: Database session
        
    Returns:
        dict: Status information
    """
    # Get policy
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise EmbeddingError(
            f"Policy not found: {policy_id}",
            details={"policy_id": policy_id}
        )
    
    # Get processing record
    proc_stmt = select(PolicyProcessing).where(
        PolicyProcessing.policy_id == policy.id,
        PolicyProcessing.stage == ProcessingStage.EMBEDDING
    )
    proc_result = await db.execute(proc_stmt)
    processing_record = proc_result.scalar_one_or_none()
    
    if not processing_record:
        return {
            "policy_id": policy_id,
            "status": "not_started",
            "message": "Embedding generation has not been initiated"
        }
    
    return {
        "policy_id": policy_id,
        "processing_id": processing_record.id,
        "status": processing_record.status.value,
        "progress_percent": processing_record.progress_percent,
        "started_at": processing_record.started_at.isoformat() if processing_record.started_at else None,
        "completed_at": processing_record.completed_at.isoformat() if processing_record.completed_at else None,
        "error_message": processing_record.error_message,
        "result_data": processing_record.result_data
    }
