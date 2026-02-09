"""
Text chunking service for policy documents.
Handles breaking down long documents into manageable chunks with overlap.
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.policy import Policy, PolicyChunk, PolicyProcessing, ProcessingStage, ProcessingStatus
from app.core.exceptions import CivicLensException
from app.constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    MIN_CHUNK_SIZE,
    MAX_CHUNK_SIZE,
    MIN_CHUNK_OVERLAP,
    MAX_CHUNK_OVERLAP,
)


logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Represents a text chunk with metadata."""
    text: str
    start_char: int
    end_char: int
    chunk_index: int
    metadata: Optional[Dict] = None


class ChunkingError(CivicLensException):
    """Exception raised when text chunking fails."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details or {}
        )


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using simple regex.
    
    Args:
        text: Input text to split
        
    Returns:
        List of sentences
    """
    # Simple sentence boundary detection
    # Matches periods, exclamation marks, or question marks followed by whitespace or end of string
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$'
    sentences = re.split(sentence_pattern, text)
    
    # Filter out empty sentences and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP
) -> List[TextChunk]:
    """
    Chunk text with sentence-aware boundaries and overlap.
    
    Args:
        text: Text to chunk
        chunk_size: Target size for each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of TextChunk objects
        
    Raises:
        ChunkingError: If chunking fails
    """
    try:
        logger.info(f"Chunking text: {len(text)} chars, chunk_size={chunk_size}, overlap={overlap}")
        
        # Validate parameters
        if chunk_size < MIN_CHUNK_SIZE or chunk_size > MAX_CHUNK_SIZE:
            raise ChunkingError(
                f"Chunk size must be between {MIN_CHUNK_SIZE} and {MAX_CHUNK_SIZE}",
                details={"chunk_size": chunk_size}
            )
        
        if overlap < MIN_CHUNK_OVERLAP or overlap > MAX_CHUNK_OVERLAP:
            raise ChunkingError(
                f"Overlap must be between {MIN_CHUNK_OVERLAP} and {MAX_CHUNK_OVERLAP}",
                details={"overlap": overlap}
            )
        
        if overlap >= chunk_size:
            raise ChunkingError(
                "Overlap must be less than chunk size",
                details={"chunk_size": chunk_size, "overlap": overlap}
            )
        
        if not text.strip():
            raise ChunkingError("Cannot chunk empty text")
        
        chunks = []
        sentences = split_into_sentences(text)
        
        if not sentences:
            # Fallback: treat entire text as one sentence
            sentences = [text]
        
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if current_chunk and len(current_chunk) + len(sentence) + 1 > chunk_size:
                # Save current chunk
                chunk_text = current_chunk.strip()
                chunks.append(TextChunk(
                    text=chunk_text,
                    start_char=current_start,
                    end_char=current_start + len(chunk_text),
                    chunk_index=chunk_index,
                    metadata={"sentence_count": len(split_into_sentences(chunk_text))}
                ))
                
                # Start new chunk with overlap
                if overlap > 0:
                    # Take last 'overlap' characters from current chunk
                    overlap_text = current_chunk[-overlap:].strip()
                    current_start = current_start + len(current_chunk) - len(overlap_text)
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_start = current_start + len(current_chunk)
                    current_chunk = sentence
                
                chunk_index += 1
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add final chunk if any text remains
        if current_chunk.strip():
            chunk_text = current_chunk.strip()
            chunks.append(TextChunk(
                text=chunk_text,
                start_char=current_start,
                end_char=current_start + len(chunk_text),
                chunk_index=chunk_index,
                metadata={"sentence_count": len(split_into_sentences(chunk_text))}
            ))
        
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
        
    except ChunkingError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during chunking: {str(e)}", exc_info=True)
        raise ChunkingError(
            f"Failed to chunk text: {str(e)}",
            details={"text_length": len(text)}
        )


async def process_policy_chunking(
    policy_id: str,
    db: AsyncSession,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
    force: bool = False
) -> Dict:
    """
    Process text chunking for a policy document.
    
    Args:
        policy_id: Unique policy identifier
        db: Database session
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks in characters
        force: If True, re-chunk even if already chunked
        
    Returns:
        dict: Chunking result with statistics
        
    Raises:
        ChunkingError: If chunking fails
    """
    logger.info(f"Processing chunking for policy: {policy_id}")
    
    # Get policy from database
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise ChunkingError(
            f"Policy not found: {policy_id}",
            details={"policy_id": policy_id}
        )
    
    # Get extracted text from processing record
    text_proc_stmt = select(PolicyProcessing).where(
        PolicyProcessing.policy_id == policy.id,
        PolicyProcessing.stage == ProcessingStage.TEXT_EXTRACTION,
        PolicyProcessing.status == ProcessingStatus.COMPLETED
    )
    text_proc_result = await db.execute(text_proc_stmt)
    text_processing = text_proc_result.scalar_one_or_none()
    
    if not text_processing or not text_processing.result_data:
        raise ChunkingError(
            "Cannot chunk: text not extracted yet",
            details={"policy_id": policy_id}
        )
    
    extracted_text = text_processing.result_data.get("extracted_text")
    if not extracted_text:
        raise ChunkingError(
            "No extracted text found",
            details={"policy_id": policy_id}
        )
    
    # Check for existing chunking processing record
    chunk_proc_stmt = select(PolicyProcessing).where(
        PolicyProcessing.policy_id == policy.id,
        PolicyProcessing.stage == ProcessingStage.CHUNKING
    )
    chunk_proc_result = await db.execute(chunk_proc_stmt)
    processing_record = chunk_proc_result.scalar_one_or_none()
    
    # Check if already chunked (unless force=True)
    if processing_record and not force:
        if processing_record.status == ProcessingStatus.COMPLETED:
            raise ChunkingError(
                "Text has already been chunked. Use force=true to re-chunk.",
                details={"policy_id": policy_id, "processing_id": processing_record.id}
            )
        elif processing_record.status == ProcessingStatus.IN_PROGRESS:
            raise ChunkingError(
                "Text chunking is already in progress",
                details={"policy_id": policy_id, "processing_id": processing_record.id}
            )
    
    # Create or update processing record
    if not processing_record:
        processing_record = PolicyProcessing(
            policy_id=policy.id,
            stage=ProcessingStage.CHUNKING,
            status=ProcessingStatus.IN_PROGRESS,
            progress_percent=0,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(processing_record)
    else:
        # Reset for re-chunking
        processing_record.status = ProcessingStatus.IN_PROGRESS
        processing_record.progress_percent = 0
        processing_record.started_at = datetime.utcnow()
        processing_record.error_message = None
        processing_record.result_data = None
        
        # Delete existing chunks
        delete_stmt = delete(PolicyChunk).where(PolicyChunk.policy_id == policy.id)
        await db.execute(delete_stmt)
    
    await db.commit()
    await db.refresh(processing_record)
    
    try:
        # Chunk the text
        chunks = chunk_text(extracted_text, chunk_size=chunk_size, overlap=overlap)
        
        # Store chunks in database
        db_chunks = []
        for chunk in chunks:
            db_chunk = PolicyChunk(
                policy_id=policy.id,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.text,
                chunk_size=len(chunk.text),
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                page_numbers=None,  # TODO: Map to page numbers if available
                metadata_json=chunk.metadata,
                created_at=datetime.utcnow()
            )
            db_chunks.append(db_chunk)
        
        db.add_all(db_chunks)
        
        # Calculate statistics
        chunk_sizes = [len(c.text) for c in chunks]
        avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
        
        result_data = {
            "chunk_count": len(chunks),
            "chunk_size_config": chunk_size,
            "overlap_config": overlap,
            "avg_chunk_size": int(avg_chunk_size),
            "min_chunk_size": min(chunk_sizes) if chunk_sizes else 0,
            "max_chunk_size": max(chunk_sizes) if chunk_sizes else 0,
            "total_characters": len(extracted_text),
            "chunking_timestamp": datetime.utcnow().isoformat()
        }
        
        # Update processing record
        processing_record.status = ProcessingStatus.COMPLETED
        processing_record.progress_percent = 100
        processing_record.completed_at = datetime.utcnow()
        processing_record.result_data = result_data
        
        await db.commit()
        await db.refresh(processing_record)
        
        logger.info(f"Chunking completed for policy: {policy_id}, created {len(chunks)} chunks")
        
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
        
        logger.error(f"Chunking failed for policy {policy_id}: {str(e)}", exc_info=True)
        
        raise ChunkingError(
            f"Text chunking failed: {str(e)}",
            details={"policy_id": policy_id, "processing_id": processing_record.id}
        )


async def get_policy_chunks(
    policy_id: str,
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0
) -> List[PolicyChunk]:
    """
    Retrieve chunks for a policy with pagination.
    
    Args:
        policy_id: Unique policy identifier
        db: Database session
        limit: Maximum number of chunks to return
        offset: Number of chunks to skip
        
    Returns:
        List of PolicyChunk objects
    """
    logger.info(f"Retrieving chunks for policy: {policy_id}, limit={limit}, offset={offset}")
    
    # Get policy
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise ChunkingError(
            f"Policy not found: {policy_id}",
            details={"policy_id": policy_id}
        )
    
    # Get chunks
    chunks_stmt = select(PolicyChunk).where(
        PolicyChunk.policy_id == policy.id
    ).order_by(PolicyChunk.chunk_index).limit(limit).offset(offset)
    
    chunks_result = await db.execute(chunks_stmt)
    chunks = chunks_result.scalars().all()
    
    logger.info(f"Retrieved {len(chunks)} chunks for policy: {policy_id}")
    
    return chunks


async def get_chunk_by_index(
    policy_id: str,
    chunk_index: int,
    db: AsyncSession
) -> Optional[PolicyChunk]:
    """
    Get a specific chunk by index.
    
    Args:
        policy_id: Unique policy identifier
        chunk_index: Index of the chunk to retrieve
        db: Database session
        
    Returns:
        PolicyChunk object or None if not found
    """
    logger.info(f"Retrieving chunk {chunk_index} for policy: {policy_id}")
    
    # Get policy
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise ChunkingError(
            f"Policy not found: {policy_id}",
            details={"policy_id": policy_id}
        )
    
    # Get chunk
    chunk_stmt = select(PolicyChunk).where(
        PolicyChunk.policy_id == policy.id,
        PolicyChunk.chunk_index == chunk_index
    )
    chunk_result = await db.execute(chunk_stmt)
    chunk = chunk_result.scalar_one_or_none()
    
    return chunk


async def get_chunk_count(policy_id: str, db: AsyncSession) -> int:
    """
    Get total number of chunks for a policy.
    
    Args:
        policy_id: Unique policy identifier
        db: Database session
        
    Returns:
        Total chunk count
    """
    # Get policy
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise ChunkingError(
            f"Policy not found: {policy_id}",
            details={"policy_id": policy_id}
        )
    
    # Count chunks
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(PolicyChunk).where(
        PolicyChunk.policy_id == policy.id
    )
    count_result = await db.execute(count_stmt)
    count = count_result.scalar()
    
    return count or 0
