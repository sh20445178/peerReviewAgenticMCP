"""
Data models for the Peer Review MCP Server.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ReviewStatus(str, Enum):
    """Enum for review statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    MERGED = "merged"


class PriorityLevel(str, Enum):
    """Enum for priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CheckStatus(str, Enum):
    """Enum for automated check statuses."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"


# Database Models

class Repository(Base):
    """Repository model for storing git repository information."""
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(255), unique=True, nullable=False, index=True)
    clone_url = Column(String(500), nullable=False)
    default_branch = Column(String(100), default="main")
    owner = Column(String(255), nullable=False)
    is_private = Column(Boolean, default=False)
    github_id = Column(Integer, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pull_requests = relationship("PullRequest", back_populates="repository")
    review_criteria = relationship("ReviewCriteria", back_populates="repository")


class PullRequest(Base):
    """Pull request model for storing PR information."""
    __tablename__ = "pull_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    pr_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(255), nullable=False)
    source_branch = Column(String(255), nullable=False)
    target_branch = Column(String(255), nullable=False)
    status = Column(String(50), default=ReviewStatus.PENDING)
    priority = Column(String(20), default=PriorityLevel.MEDIUM)
    labels = Column(JSON, default=list)
    github_id = Column(Integer, nullable=True)
    github_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="pull_requests")
    reviews = relationship("Review", back_populates="pull_request")
    automated_checks = relationship("AutomatedCheck", back_populates="pull_request")
    governance_validation = relationship("GovernanceValidation", back_populates="pull_request")


class Review(Base):
    """Review model for storing review information."""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    pull_request_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)
    reviewer = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    comments = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)  # Numerical score if applicable
    review_criteria_met = Column(JSON, default=dict)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pull_request = relationship("PullRequest", back_populates="reviews")


class AutomatedCheck(Base):
    """Automated check model for storing CI/CD and tool results."""
    __tablename__ = "automated_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    pull_request_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)
    check_type = Column(String(100), nullable=False)  # build, test, code_quality, security, etc.
    check_name = Column(String(255), nullable=False)
    status = Column(String(50), default=CheckStatus.PENDING)
    details = Column(JSON, default=dict)
    external_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    pull_request = relationship("PullRequest", back_populates="automated_checks")


class ReviewCriteria(Base):
    """Review criteria model for storing governance rules."""
    __tablename__ = "review_criteria"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    criteria_type = Column(String(100), nullable=False)  # code_quality, security, performance, etc.
    rules = Column(JSON, nullable=False)
    is_required = Column(Boolean, default=True)
    weight = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="review_criteria")


class GovernanceValidation(Base):
    """Governance validation model for storing compliance checks."""
    __tablename__ = "governance_validations"
    
    id = Column(Integer, primary_key=True, index=True)
    pull_request_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)
    validation_type = Column(String(100), nullable=False)
    is_compliant = Column(Boolean, nullable=False)
    violations = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    validated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pull_request = relationship("PullRequest", back_populates="governance_validation")


# Pydantic Models for API

class RepositoryBase(BaseModel):
    """Base repository schema."""
    name: str
    full_name: str
    clone_url: str
    default_branch: str = "main"
    owner: str
    is_private: bool = False


class RepositoryCreate(RepositoryBase):
    """Repository creation schema."""
    github_id: Optional[int] = None


class RepositoryResponse(RepositoryBase):
    """Repository response schema."""
    id: int
    github_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PullRequestBase(BaseModel):
    """Base pull request schema."""
    pr_number: int
    title: str
    description: Optional[str] = None
    author: str
    source_branch: str
    target_branch: str
    priority: PriorityLevel = PriorityLevel.MEDIUM
    labels: List[str] = Field(default_factory=list)


class PullRequestCreate(PullRequestBase):
    """Pull request creation schema."""
    repository_id: int
    github_id: Optional[int] = None
    github_url: Optional[str] = None


class PullRequestResponse(PullRequestBase):
    """Pull request response schema."""
    id: int
    repository_id: int
    status: ReviewStatus
    github_id: Optional[int]
    github_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReviewBase(BaseModel):
    """Base review schema."""
    reviewer: str
    status: ReviewStatus
    comments: Optional[str] = None
    score: Optional[int] = None
    review_criteria_met: Dict[str, Any] = Field(default_factory=dict)


class ReviewCreate(ReviewBase):
    """Review creation schema."""
    pull_request_id: int


class ReviewResponse(ReviewBase):
    """Review response schema."""
    id: int
    pull_request_id: int
    submitted_at: datetime
    
    class Config:
        from_attributes = True


class AutomatedCheckBase(BaseModel):
    """Base automated check schema."""
    check_type: str
    check_name: str
    status: CheckStatus = CheckStatus.PENDING
    details: Dict[str, Any] = Field(default_factory=dict)
    external_url: Optional[str] = None


class AutomatedCheckCreate(AutomatedCheckBase):
    """Automated check creation schema."""
    pull_request_id: int


class AutomatedCheckResponse(AutomatedCheckBase):
    """Automated check response schema."""
    id: int
    pull_request_id: int
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ReviewCriteriaBase(BaseModel):
    """Base review criteria schema."""
    name: str
    description: Optional[str] = None
    criteria_type: str
    rules: Dict[str, Any]
    is_required: bool = True
    weight: int = 1


class ReviewCriteriaCreate(ReviewCriteriaBase):
    """Review criteria creation schema."""
    repository_id: int


class ReviewCriteriaResponse(ReviewCriteriaBase):
    """Review criteria response schema."""
    id: int
    repository_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GovernanceValidationBase(BaseModel):
    """Base governance validation schema."""
    validation_type: str
    is_compliant: bool
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)


class GovernanceValidationCreate(GovernanceValidationBase):
    """Governance validation creation schema."""
    pull_request_id: int


class GovernanceValidationResponse(GovernanceValidationBase):
    """Governance validation response schema."""
    id: int
    pull_request_id: int
    validated_at: datetime
    
    class Config:
        from_attributes = True


# MCP Tool Schemas

class ReviewSummary(BaseModel):
    """Summary of a pull request review."""
    pull_request_id: int
    pr_number: int
    title: str
    author: str
    status: ReviewStatus
    priority: PriorityLevel
    reviews_count: int
    automated_checks_passed: int
    automated_checks_total: int
    compliance_score: float
    recommendations: List[str]


class ReviewMetrics(BaseModel):
    """Metrics for review performance."""
    total_pull_requests: int
    avg_review_time_hours: float
    compliance_rate: float
    automation_success_rate: float
    top_violation_types: List[Dict[str, Any]]