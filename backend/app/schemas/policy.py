"""
Pydantic schemas for policy API endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum


class PolicyTypeEnum(str, Enum):
    """Policy category types."""
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    AGRICULTURE = "agriculture"
    EMPLOYMENT = "employment"
    HOUSING = "housing"
    SOCIAL_WELFARE = "social_welfare"
    INFRASTRUCTURE = "infrastructure"
    ENVIRONMENT = "environment"
    FINANCE = "finance"
    OTHER = "other"


class PolicyStatusEnum(str, Enum):
    """Policy processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"
    ARCHIVED = "archived"


# Base schemas
class PolicyBase(BaseModel):
    """Base policy schema with common fields."""
    title: Optional[str] = Field(None, max_length=500, description="Policy document title")
    description: Optional[str] = Field(None, description="Brief description of the policy")
    language: Optional[str] = Field("en", max_length=10, description="ISO 639-1 language code")
    jurisdiction: Optional[str] = Field(None, max_length=100, description="Geographic scope")
    policy_type: Optional[PolicyTypeEnum] = Field(None, description="Policy category")
    effective_date: Optional[datetime] = Field(None, description="When policy becomes active")
    expiry_date: Optional[datetime] = Field(None, description="When policy expires")
    source_url: Optional[str] = Field(None, max_length=500, description="Original source URL")


class PolicyCreate(PolicyBase):
    """Schema for creating a new policy (internal use)."""
    filename: str = Field(..., max_length=255, description="Original filename")
    file_path: str = Field(..., max_length=500, description="Storage path")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    file_hash: Optional[str] = Field(None, max_length=64, description="SHA-256 hash")
    content_type: str = Field(default="application/pdf", max_length=100)
    policy_id: str = Field(..., max_length=50, description="Unique policy identifier")


class PolicyUpdate(BaseModel):
    """Schema for updating policy metadata."""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    language: Optional[str] = Field(None, max_length=10)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    policy_type: Optional[PolicyTypeEnum] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    source_url: Optional[str] = Field(None, max_length=500)
    status: Optional[PolicyStatusEnum] = None


class PolicyInDB(PolicyBase):
    """Full policy representation from database."""
    id: int
    policy_id: str
    filename: str
    file_path: str
    file_size: int
    file_hash: Optional[str]
    content_type: str
    version: int
    status: PolicyStatusEnum
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class PolicyPublic(PolicyBase):
    """Public API response for policy."""
    id: int
    policy_id: str
    filename: str
    file_size: int
    content_type: str
    status: PolicyStatusEnum
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PolicyUploadResponse(BaseModel):
    """Response model for policy document upload."""
    id: int = Field(..., description="Database ID")
    policy_id: str = Field(..., description="Unique identifier for the uploaded policy")
    filename: str = Field(..., description="Original filename of the uploaded document")
    file_size: int = Field(..., description="Size of the file in bytes")
    content_type: str = Field(..., description="MIME type of the uploaded file")
    upload_timestamp: datetime = Field(..., description="Timestamp when the file was uploaded")
    storage_path: str = Field(..., description="Path where the file is stored")
    status: str = Field(default="uploaded", description="Upload status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "policy_id": "pol_abc123xyz",
                "filename": "healthcare_policy_2024.pdf",
                "file_size": 2048576,
                "content_type": "application/pdf",
                "upload_timestamp": "2024-01-27T18:00:00Z",
                "storage_path": "uploads/policies/pol_abc123xyz.pdf",
                "status": "uploaded"
            }
        }
    )


class PolicyListResponse(BaseModel):
    """Response for policy list endpoint."""
    policies: List[PolicyPublic]
    total: int
    limit: int
    offset: int


class PolicyFilter(BaseModel):
    """Query parameters for filtering policies."""
    status: Optional[PolicyStatusEnum] = None
    policy_type: Optional[PolicyTypeEnum] = None
    jurisdiction: Optional[str] = None
    language: Optional[str] = None
    search: Optional[str] = Field(None, description="Full-text search query")
    limit: int = Field(default=20, ge=1, le=100, description="Number of results per page")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class PolicyMetadata(BaseModel):
    """Metadata for an uploaded policy document."""
    id: str
    filename: str
    file_size: int
    upload_timestamp: datetime
    description: Optional[str] = None
