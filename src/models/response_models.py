"""Response data models for AuraStream API."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, validator


class SentimentAnalysisResponse(BaseModel):
    """Response model for sentiment analysis."""

    sentiment: str = Field(..., description="Sentiment classification")
    score: float = Field(..., ge=0.0, le=1.0, description="Sentiment score")
    language_code: Optional[str] = Field(None, description="Language code")
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score"
    )
    pii_detected: Optional[bool] = Field(None, description="Whether PII was detected")
    processing_time_ms: Optional[int] = Field(
        None, description="Processing time in milliseconds"
    )
    cache_hit: Optional[bool] = Field(
        None, description="Whether result was served from cache"
    )
    request_id: Optional[str] = Field(None, description="Unique request identifier")

    @validator("sentiment")
    @classmethod
    def validate_sentiment(cls, v: str) -> str:
        """Validate sentiment value."""
        valid_sentiments = ["POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED"]
        if v not in valid_sentiments:
            raise ValueError(f"Sentiment must be one of {valid_sentiments}")
        return v


class AsyncJobResponse(BaseModel):
    """Response model for asynchronous job creation."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    message: Optional[str] = Field(None, description="Status message")
    estimated_completion: Optional[str] = Field(
        None, description="Estimated completion time"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Job creation time",
    )

    @validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        valid_statuses = ["SUBMITTED", "PROCESSING", "COMPLETED", "FAILED"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Job creation time",
    )
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    result: Optional[SentimentAnalysisResponse] = Field(
        None, description="Analysis result"
    )
    error: Optional[Dict[str, Any]] = Field(None, description="Error information")
    source_id: Optional[str] = Field(None, description="Source identifier")
    progress: Optional[int] = Field(None, description="Job progress percentage")

    @validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        valid_statuses = ["PROCESSING", "COMPLETED", "FAILED"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Check timestamp",
    )
    version: str = Field(..., description="Service version")
    components: Dict[str, str] = Field(..., description="Component status")

    @validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate health status value."""
        valid_statuses = ["healthy", "unhealthy", "degraded"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: Union[str, Dict[str, Any]] = Field(..., description="Error information")
    message: Optional[str] = Field(None, description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")

    @validator("error")
    @classmethod
    def validate_error(cls, v: Union[str, Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """Validate error field."""
        if isinstance(v, str):
            return v
        elif isinstance(v, dict):
            return v
        else:
            raise ValueError("Error must be a string or dictionary")
        return v
