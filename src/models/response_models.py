"""Response data models for AuraStream API."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class SentimentAnalysisResponse(BaseModel):
    """Response model for sentiment analysis."""
    
    sentiment: str = Field(..., description="Sentiment classification")
    score: float = Field(..., ge=0.0, le=1.0, description="Sentiment score")
    language_code: Optional[str] = Field(None, description="Language code")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    pii_detected: Optional[bool] = Field(None, description="Whether PII was detected")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    cache_hit: Optional[bool] = Field(None, description="Whether result was served from cache")
    request_id: Optional[str] = Field(None, description="Unique request identifier")


class AsyncJobResponse(BaseModel):
    """Response model for asynchronous job creation."""
    
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Job creation time")


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    created_at: datetime = Field(..., description="Job creation time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    result: Optional[SentimentAnalysisResponse] = Field(None, description="Analysis result")
    error: Optional[Dict[str, Any]] = Field(None, description="Error information")
    source_id: Optional[str] = Field(None, description="Source identifier")


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Check timestamp")
    version: str = Field(..., description="Service version")
    components: Dict[str, str] = Field(..., description="Component status")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    
    error: Dict[str, Any] = Field(..., description="Error information")
