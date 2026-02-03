"""
Text extraction service for policy documents.
Handles PDF text extraction and processing pipeline integration.
"""

from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import logging

from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.policy import Policy, PolicyProcessing, ProcessingStage, ProcessingStatus
from app.core.exceptions import CivicLensException


logger = logging.getLogger(__name__)


class TextExtractionError(CivicLensException):
    """Exception raised when text extraction fails."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details or {}
        )


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extract raw text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Extracted text content
        
    Raises:
        TextExtractionError: If extraction fails
    """
    try:
        logger.info(f"Starting text extraction from: {file_path}")
        
        if not file_path.exists():
            raise TextExtractionError(
                message="PDF file not found",
                details={"file_path": str(file_path)}
            )
        
        # Read PDF and extract text
        reader = PdfReader(str(file_path))
        
        # Check if PDF is encrypted
        if reader.is_encrypted:
            raise TextExtractionError(
                message="PDF is encrypted and cannot be processed",
                details={"file_path": str(file_path)}
            )
        
        # Extract text from all pages
        text_content = []
        total_pages = len(reader.pages)
        
        logger.debug(f"Extracting text from {total_pages} pages")
        
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
                logger.debug(f"Extracted text from page {page_num}/{total_pages}")
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num}: {str(e)}")
                # Continue with other pages even if one fails
                continue
        
        # Combine all text
        full_text = "\n\n".join(text_content)
        
        if not full_text.strip():
            raise TextExtractionError(
                message="No text content found in PDF",
                details={"file_path": str(file_path), "pages": total_pages}
            )
        
        logger.info(f"Successfully extracted {len(full_text)} characters from {total_pages} pages")
        
        return full_text.strip()
        
    except TextExtractionError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during text extraction: {str(e)}", exc_info=True)
        raise TextExtractionError(
            message=f"Failed to extract text from PDF: {str(e)}",
            details={"file_path": str(file_path)}
        )


async def process_policy_text_extraction(
    policy_id: str,
    db: AsyncSession,
    force: bool = False
) -> Dict:
    """
    Process text extraction for a policy document.
    Creates/updates PolicyProcessing record and extracts text.
    
    Args:
        policy_id: Unique policy identifier
        db: Database session
        force: If True, re-extract even if already extracted
        
    Returns:
        dict: Processing result with extracted text and metadata
        
    Raises:
        TextExtractionError: If extraction fails
    """
    logger.info(f"Processing text extraction for policy: {policy_id}")
    
    # Get policy from database
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise TextExtractionError(
            message=f"Policy not found: {policy_id}",
            details={"policy_id": policy_id}
        )
    
    # Check for existing processing record
    proc_stmt = select(PolicyProcessing).where(
        PolicyProcessing.policy_id == policy.id,
        PolicyProcessing.stage == ProcessingStage.TEXT_EXTRACTION
    )
    proc_result = await db.execute(proc_stmt)
    processing_record = proc_result.scalar_one_or_none()
    
    # Check if already extracted (unless force=True)
    if processing_record and not force:
        if processing_record.status == ProcessingStatus.COMPLETED:
            raise TextExtractionError(
                message="Text has already been extracted. Use force=true to re-extract.",
                details={"policy_id": policy_id, "processing_id": processing_record.id}
            )
        elif processing_record.status == ProcessingStatus.IN_PROGRESS:
            raise TextExtractionError(
                message="Text extraction is already in progress",
                details={"policy_id": policy_id, "processing_id": processing_record.id}
            )
    
    # Create or update processing record
    if not processing_record:
        processing_record = PolicyProcessing(
            policy_id=policy.id,
            stage=ProcessingStage.TEXT_EXTRACTION,
            status=ProcessingStatus.IN_PROGRESS,
            progress_percent=0,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(processing_record)
    else:
        # Reset for re-extraction
        processing_record.status = ProcessingStatus.IN_PROGRESS
        processing_record.progress_percent = 0
        processing_record.started_at = datetime.utcnow()
        processing_record.error_message = None
        processing_record.result_data = None
    
    await db.commit()
    await db.refresh(processing_record)
    
    try:
        # Extract text from PDF
        file_path = Path(policy.file_path)
        extracted_text = extract_text_from_pdf(file_path)
        
        # Store result
        result_data = {
            "extracted_text": extracted_text,
            "character_count": len(extracted_text),
            "word_count": len(extracted_text.split()),
            "extraction_timestamp": datetime.utcnow().isoformat()
        }
        
        # Update processing record
        processing_record.status = ProcessingStatus.COMPLETED
        processing_record.progress_percent = 100
        processing_record.completed_at = datetime.utcnow()
        processing_record.result_data = result_data
        
        await db.commit()
        await db.refresh(processing_record)
        
        logger.info(f"Text extraction completed for policy: {policy_id}")
        
        return {
            "policy_id": policy_id,
            "processing_id": processing_record.id,
            "status": "completed",
            "character_count": result_data["character_count"],
            "word_count": result_data["word_count"],
            "text_preview": extracted_text[:500] if len(extracted_text) > 500 else extracted_text
        }
        
    except Exception as e:
        # Update processing record with error
        processing_record.status = ProcessingStatus.FAILED
        processing_record.error_message = str(e)
        processing_record.completed_at = datetime.utcnow()
        
        await db.commit()
        
        logger.error(f"Text extraction failed for policy {policy_id}: {str(e)}", exc_info=True)
        
        raise TextExtractionError(
            message=f"Text extraction failed: {str(e)}",
            details={"policy_id": policy_id, "processing_id": processing_record.id}
        )


async def get_extracted_text(policy_id: str, db: AsyncSession) -> Optional[str]:
    """
    Retrieve extracted text for a policy.
    
    Args:
        policy_id: Unique policy identifier
        db: Database session
        
    Returns:
        str: Extracted text content, or None if not extracted
    """
    logger.info(f"Retrieving extracted text for policy: {policy_id}")
    
    # Get policy
    stmt = select(Policy).where(
        Policy.policy_id == policy_id,
        Policy.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise TextExtractionError(
            message=f"Policy not found: {policy_id}",
            details={"policy_id": policy_id}
        )
    
    # Get processing record
    proc_stmt = select(PolicyProcessing).where(
        PolicyProcessing.policy_id == policy.id,
        PolicyProcessing.stage == ProcessingStage.TEXT_EXTRACTION,
        PolicyProcessing.status == ProcessingStatus.COMPLETED
    )
    proc_result = await db.execute(proc_stmt)
    processing_record = proc_result.scalar_one_or_none()
    
    if not processing_record or not processing_record.result_data:
        return None
    
    return processing_record.result_data.get("extracted_text")
