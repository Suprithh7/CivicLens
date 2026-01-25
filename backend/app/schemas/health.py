from pydantic import BaseModel
from typing import Dict


class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str
    app_name: str
    version: str
    environment: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "app_name": "CivicLens AI",
                "version": "0.1.0",
                "environment": "development"
            }
        }
