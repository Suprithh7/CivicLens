"""
Pydantic schemas for policy simplification endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ExplanationType(str, Enum):
    """Types of policy explanations available."""
    EXPLANATION = "explanation"
    ELIGIBILITY = "eligibility"
    KEY_POINTS = "key_points"
    BENEFITS = "benefits"
    APPLICATION = "application"
    SCENARIO = "scenario"


class SimplificationRequest(BaseModel):
    """Request schema for policy simplification."""
    
    policy_id: str = Field(
        ...,
        description="Unique identifier of the policy to simplify",
        examples=["pol_abc123"]
    )
    
    explanation_type: ExplanationType = Field(
        default=ExplanationType.EXPLANATION,
        description="Type of explanation to generate"
    )
    
    user_situation: Optional[str] = Field(
        None,
        description="User's situation for eligibility checks (required for 'eligibility' type)",
        max_length=2000,
        examples=["I'm a single parent making $35,000/year with two kids"]
    )
    
    focus_area: Optional[str] = Field(
        None,
        description="Specific aspect to focus on (optional for 'explanation' type)",
        max_length=200,
        examples=["eligibility criteria", "application process", "benefits"]
    )
    
    max_points: int = Field(
        default=5,
        description="Maximum number of key points to extract (for 'key_points' type)",
        ge=1,
        le=10
    )
    
    temperature: Optional[float] = Field(
        None,
        description="LLM sampling temperature (0.0-2.0). Lower is more focused, higher is more creative.",
        ge=0.0,
        le=2.0
    )
    
    model: Optional[str] = Field(
        None,
        description="LLM model to use. If not provided, uses default from config.",
        examples=["gpt-4-turbo-preview", "gpt-3.5-turbo"]
    )
    
    language: Optional[str] = Field(
        None,
        description="Language code for the response (e.g., 'en', 'es', 'fr'). If not provided, auto-detects from user_situation or focus_area.",
        examples=["en", "es", "fr", "hi", "zh-cn"]
    )
    
    scenario_type: Optional[str] = Field(
        None,
        description="User scenario type for scenario-based explanations (required for 'scenario' type)",
        examples=["student", "senior_citizen", "small_business_owner", "parent", "low_income", "veteran", "disabled", "first_time_homebuyer", "unemployed", "general_citizen"]
    )
    
    scenario_details: Optional[str] = Field(
        None,
        description="Additional details about the user's scenario (optional for 'scenario' type)",
        max_length=1000,
        examples=["20 years old, full-time college student with part-time job", "65+ years old, retired, living on fixed income"]
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "policy_id": "pol_abc123",
                    "explanation_type": "explanation",
                    "focus_area": "eligibility criteria",
                    "temperature": 0.7,
                    "language": "en"
                },
                {
                    "policy_id": "pol_abc123",
                    "explanation_type": "scenario",
                    "scenario_type": "student",
                    "scenario_details": "20 years old, full-time college student",
                    "language": "en"
                }
            ]
        }


class SimplificationResponse(BaseModel):
    """Response schema for policy simplification."""
    
    policy_id: str = Field(..., description="Policy identifier")
    policy_title: Optional[str] = Field(None, description="Title of the policy document")
    explanation_type: str = Field(..., description="Type of explanation provided")
    simplified_text: str = Field(..., description="The simplified, plain-language explanation")
    model_used: str = Field(..., description="LLM model used for generation")
    timestamp: str = Field(..., description="ISO timestamp of when the explanation was generated")
    detected_language: str = Field(..., description="Detected language code from the request")
    response_language: str = Field(..., description="Language code of the response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "policy_id": "pol_abc123",
                "policy_title": "Affordable Housing Policy 2024",
                "explanation_type": "explanation",
                "simplified_text": "This policy helps low-income families afford housing...",
                "model_used": "gpt-4-turbo-preview",
                "timestamp": "2026-02-13T22:26:00Z",
                "detected_language": "en",
                "response_language": "en"
            }
        }
