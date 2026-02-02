"""
File-related utility functions.
Provides helpers for file validation, hashing, and manipulation.
"""

import hashlib
import secrets
import string
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status

from app.constants import (
    MAX_FILE_SIZE_BYTES,
    ALLOWED_FILE_EXTENSIONS,
    ALLOWED_CONTENT_TYPES,
    HASH_ALGORITHM,
    HASH_BUFFER_SIZE,
    POLICY_ID_PREFIX,
    POLICY_ID_LENGTH,
    ERROR_FILE_TOO_LARGE,
    ERROR_INVALID_FILE_TYPE,
)


def validate_file_type(file: UploadFile, allowed_extensions: set = ALLOWED_FILE_EXTENSIONS) -> None:
    """
    Validate that the uploaded file has an allowed extension and content type.
    
    Args:
        file: The uploaded file to validate
        allowed_extensions: Set of allowed file extensions (with dots)
        
    Raises:
        HTTPException: If file type is not allowed
    """
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_INVALID_FILE_TYPE
        )
    
    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_INVALID_FILE_TYPE
        )


def validate_file_size(file_size: int, max_size: int = MAX_FILE_SIZE_BYTES) -> None:
    """
    Validate that the file size is within allowed limits.
    
    Args:
        file_size: Size of the file in bytes
        max_size: Maximum allowed size in bytes
        
    Raises:
        HTTPException: If file size exceeds maximum
    """
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_FILE_TOO_LARGE.format(max_size=max_size_mb)
        )


def validate_pdf(file: UploadFile) -> None:
    """
    Validate uploaded file is a PDF and within size limits.
    
    Args:
        file: The uploaded file to validate
        
    Raises:
        HTTPException: If file validation fails
    """
    validate_file_type(file)
    # Note: File size validation happens after reading content


def calculate_file_hash(content: bytes, algorithm: str = HASH_ALGORITHM) -> str:
    """
    Calculate hash of file content.
    
    Args:
        content: File content as bytes
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(content)
    return hash_obj.hexdigest()


def calculate_file_hash_chunked(file_path: Path, algorithm: str = HASH_ALGORITHM) -> str:
    """
    Calculate hash of file content using chunked reading for large files.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(HASH_BUFFER_SIZE):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable string.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def generate_unique_id(prefix: str = POLICY_ID_PREFIX, length: int = POLICY_ID_LENGTH) -> str:
    """
    Generate a unique identifier with a prefix.
    
    Args:
        prefix: Prefix for the ID (default: "pol_")
        length: Length of the random part (default: 12)
        
    Returns:
        Unique identifier string (e.g., "pol_abc123xyz789")
    """
    alphabet = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}{random_part}"


def get_file_extension(filename: str) -> str:
    """
    Get the file extension from a filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        File extension including the dot (e.g., ".pdf")
    """
    return Path(filename).suffix.lower()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove potentially dangerous characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Get the file extension
    ext = get_file_extension(filename)
    # Get the base name without extension
    base = Path(filename).stem
    
    # Replace spaces and special characters with underscores
    safe_chars = string.ascii_letters + string.digits + "-_"
    sanitized_base = ''.join(c if c in safe_chars else '_' for c in base)
    
    # Limit length
    max_length = 200
    if len(sanitized_base) > max_length:
        sanitized_base = sanitized_base[:max_length]
    
    return f"{sanitized_base}{ext}"
