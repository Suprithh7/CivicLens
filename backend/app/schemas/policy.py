from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PolicyUploadResponse(BaseModel):
    """Response model for policy document upload."""
    
    id: str = Field(..., description="Unique identifier for the uploaded policy")
    filename: str = Field(..., description="Original filename of the uploaded document")
    file_size: int = Field(..., description="Size of the file in bytes")
    content_type: str = Field(..., description="MIME type of the uploaded file")
    upload_timestamp: datetime = Field(..., description="Timestamp when the file was uploaded")
    storage_path: str = Field(..., description="Path where the file is stored")
    status: str = Field(default="uploaded", description="Upload status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "pol_abc123xyz",
                "filename": "healthcare_policy_2024.pdf",
                "file_size": 2048576,
                "content_type": "application/pdf",
                "upload_timestamp": "2024-01-27T18:00:00Z",
                "storage_path": "uploads/policies/pol_abc123xyz.pdf",
                "status": "uploaded"
            }
        }


class PolicyMetadata(BaseModel):
    """Metadata for an uploaded policy document."""
    
    id: str
    filename: str
    file_size: int
    upload_timestamp: datetime
    description: Optional[str] = None
