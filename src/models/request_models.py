"""Request data models for AuraStream API."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class SentimentAnalysisRequest(BaseModel):
    """Request model for sentiment analysis."""
    
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Analysis options")
    
    @validator('text')
    def validate_text(cls, v):
        """Validate text input."""
        if not v or not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()
    
    @validator('options')
    def validate_options(cls, v):
        """Validate options."""
        if v is None:
            return v
        
        allowed_options = [
            'language_code', 
            'include_confidence', 
            'include_pii_detection',
            'callback_url'
        ]
        
        for key in v.keys():
            if key not in allowed_options:
                raise ValueError(f'Invalid option: {key}')
        
        return v


class AsyncSentimentAnalysisRequest(BaseModel):
    """Request model for asynchronous sentiment analysis."""
    
    text: str = Field(..., min_length=1, max_length=1048576, description="Text to analyze (max 1MB)")
    source_id: Optional[str] = Field(default=None, description="Custom identifier for tracking")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Analysis options")
    
    @validator('text')
    def validate_text(cls, v):
        """Validate text input."""
        if not v or not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()
    
    @validator('options')
    def validate_options(cls, v):
        """Validate options."""
        if v is None:
            return v
        
        allowed_options = [
            'language_code', 
            'include_confidence', 
            'include_pii_detection',
            'callback_url'
        ]
        
        for key in v.keys():
            if key not in allowed_options:
                raise ValueError(f'Invalid option: {key}')
        
        return v


class JobStatusRequest(BaseModel):
    """Request model for job status check."""
    
    job_id: str = Field(..., description="Job identifier")
