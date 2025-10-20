"""Request data models for AuraStream API."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class SentimentAnalysisRequest(BaseModel):
    """Request model for sentiment analysis."""

    text: str = Field(..., max_length=5000, description="Text to analyze")
    options: Optional[Dict[str, Any]] = Field(
        default=None, description="Analysis options"
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text input."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate options."""
        if v is None:
            return v
        return v


class AsyncSentimentAnalysisRequest(BaseModel):
    """Request model for asynchronous sentiment analysis."""

    text: str = Field(..., max_length=1048576, description="Text to analyze (max 1MB)")
    source_id: Optional[str] = Field(
        default=None, description="Custom identifier for tracking"
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None, description="Analysis options"
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text input."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate options."""
        if v is None:
            return v
        return v


class JobStatusRequest(BaseModel):
    """Request model for job status check."""

    job_id: str = Field(..., description="Job identifier")

    @field_validator("job_id")
    @classmethod
    def validate_job_id(cls, v: str) -> str:
        """Validate job ID format."""
        if not v or not v.strip():
            raise ValueError("Job ID cannot be empty")
        if len(v.strip()) < 3:
            raise ValueError("Job ID must be at least 3 characters long")
        # Check for valid UUID-like format (job-xxx-xxx-xxx)
        if not v.strip().startswith("job-") or len(v.strip().split("-")) < 4:
            raise ValueError("Invalid job ID format")
        return v.strip()
