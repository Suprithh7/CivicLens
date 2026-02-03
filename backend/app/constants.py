"""
Application-wide constants.
Centralized location for all hardcoded values used across the application.
"""

from pathlib import Path

# File Upload Configuration
UPLOAD_BASE_DIR = Path("uploads")
POLICY_UPLOAD_DIR = UPLOAD_BASE_DIR / "policies"
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_EXTENSIONS = {".pdf"}
ALLOWED_CONTENT_TYPES = {"application/pdf"}

# Pagination Defaults
DEFAULT_PAGE_LIMIT = 20
MIN_PAGE_LIMIT = 1
MAX_PAGE_LIMIT = 100
DEFAULT_PAGE_OFFSET = 0

# File Hashing
HASH_ALGORITHM = "sha256"
HASH_BUFFER_SIZE = 65536  # 64KB chunks for hashing

# Policy ID Generation
POLICY_ID_PREFIX = "pol_"
POLICY_ID_LENGTH = 12  # Length of random part after prefix

# Error Messages
ERROR_FILE_TOO_LARGE = "File size exceeds maximum allowed size of {max_size}MB"
ERROR_INVALID_FILE_TYPE = "Invalid file type. Only PDF files are allowed"
ERROR_FILE_UPLOAD_FAILED = "Failed to upload file"
ERROR_POLICY_NOT_FOUND = "Policy not found"
ERROR_POLICY_ALREADY_EXISTS = "A policy with this file hash already exists"
ERROR_DATABASE_ERROR = "Database operation failed"

# Success Messages
SUCCESS_POLICY_UPLOADED = "Policy uploaded successfully"
SUCCESS_POLICY_DELETED = "Policy deleted successfully"

# Text Extraction Configuration
TEXT_PREVIEW_LENGTH = 500  # Length of text preview in API responses

# Text Extraction Messages
SUCCESS_TEXT_EXTRACTION_STARTED = "Text extraction started"
SUCCESS_TEXT_EXTRACTION_COMPLETED = "Text extraction completed successfully"
ERROR_TEXT_EXTRACTION_FAILED = "Failed to extract text from PDF"
ERROR_TEXT_EXTRACTION_IN_PROGRESS = "Text extraction already in progress"
ERROR_TEXT_ALREADY_EXTRACTED = "Text has already been extracted"
ERROR_NO_EXTRACTED_TEXT = "No extracted text found for this policy"

# Date/Time Formats
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

# Logging
LOG_FORMAT_JSON = "json"
LOG_FORMAT_TEXT = "text"
