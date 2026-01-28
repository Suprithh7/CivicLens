"""
SQLAlchemy models for policy documents and related entities.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Index, BigInteger, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
import enum

from app.core.database import Base


class PolicyStatus(str, enum.Enum):
    """Policy processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"
    ARCHIVED = "archived"


class PolicyType(str, enum.Enum):
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


class Policy(Base):
    """
    Main policy document model.
    Stores metadata for uploaded government policy documents.
    """
    __tablename__ = "policies"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Unique identifier (e.g., pol_abc123xyz)
    policy_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Basic metadata
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash
    content_type = Column(String(100), nullable=False, default="application/pdf")
    
    # Version control
    version = Column(Integer, nullable=False, default=1)
    
    # Language and jurisdiction
    language = Column(String(10), nullable=True, default="en")  # ISO 639-1 code
    jurisdiction = Column(String(100), nullable=True)  # e.g., "India", "Karnataka", "Bangalore"
    
    # Classification
    policy_type = Column(SQLEnum(PolicyType), nullable=True, index=True)
    
    # Dates
    effective_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Source information
    source_url = Column(String(500), nullable=True)
    
    # Flexible metadata storage
    metadata_json = Column(JSON, nullable=True)
    
    # Full-text search (simplified for SQLite)
    search_vector = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(
        SQLEnum(PolicyStatus), 
        nullable=False, 
        default=PolicyStatus.UPLOADED,
        index=True
    )
    
    # User tracking (for future auth implementation)
    uploaded_by_id = Column(Integer, nullable=True)  # Foreign key to users table
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    processing_records = relationship(
        "PolicyProcessing", 
        back_populates="policy",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_policy_status_type', 'status', 'policy_type'),
        Index('idx_policy_created_at', 'created_at'),
        Index('idx_policy_jurisdiction', 'jurisdiction'),
    )
    
    def __repr__(self) -> str:
        return f"<Policy(id={self.id}, policy_id={self.policy_id}, title={self.title})>"


class PolicyCategory(Base):
    """
    Hierarchical category system for policy classification.
    """
    __tablename__ = "policy_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Hierarchical structure
    parent_id = Column(Integer, ForeignKey("policy_categories.id"), nullable=True)
    parent = relationship("PolicyCategory", remote_side=[id], backref="children")
    
    # UI metadata
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<PolicyCategory(id={self.id}, name={self.name})>"


class PolicyTag(Base):
    """
    Flexible tagging system for policies.
    """
    __tablename__ = "policy_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    slug = Column(String(50), nullable=False, unique=True, index=True)
    color = Column(String(7), nullable=True)  # Hex color code
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<PolicyTag(id={self.id}, name={self.name})>"


class ProcessingStage(str, enum.Enum):
    """AI processing pipeline stages."""
    TEXT_EXTRACTION = "text_extraction"
    SUMMARIZATION = "summarization"
    EMBEDDING = "embedding"
    QA_READY = "qa_ready"


class ProcessingStatus(str, enum.Enum):
    """Processing stage status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PolicyProcessing(Base):
    """
    Track AI processing pipeline stages for each policy.
    """
    __tablename__ = "policy_processing"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    
    # Processing stage information
    stage = Column(SQLEnum(ProcessingStage), nullable=False)
    status = Column(SQLEnum(ProcessingStatus), nullable=False, default=ProcessingStatus.PENDING)
    progress_percent = Column(Integer, nullable=False, default=0)  # 0-100
    
    # Results and errors
    result_data = Column(JSON, nullable=True)  # Store stage-specific results
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    policy = relationship("Policy", back_populates="processing_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_processing_policy_stage', 'policy_id', 'stage'),
        Index('idx_processing_status', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<PolicyProcessing(id={self.id}, policy_id={self.policy_id}, stage={self.stage}, status={self.status})>"
