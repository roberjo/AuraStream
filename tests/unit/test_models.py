"""Unit tests for data models."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from src.models.request_models import (
    SentimentAnalysisRequest,
    AsyncSentimentAnalysisRequest,
    JobStatusRequest
)
from src.models.response_models import (
    SentimentAnalysisResponse,
    AsyncJobResponse,
    JobStatusResponse,
    HealthResponse,
    ErrorResponse
)


class TestSentimentAnalysisRequest:
    """Test SentimentAnalysisRequest model."""
    
    def test_valid_request(self):
        """Test valid request creation."""
        request = SentimentAnalysisRequest(
            text="I love this product!",
            source_id="test-source",
            options={"include_confidence": True}
        )
        
        assert request.text == "I love this product!"
        assert request.source_id == "test-source"
        assert request.options == {"include_confidence": True}
    
    def test_minimal_request(self):
        """Test minimal request creation."""
        request = SentimentAnalysisRequest(text="Test text")
        
        assert request.text == "Test text"
        assert request.source_id is None
        assert request.options is None
    
    def test_empty_text_validation(self):
        """Test empty text validation."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisRequest(text="")
        
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_whitespace_only_text_validation(self):
        """Test whitespace-only text validation."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisRequest(text="   \n\t   ")
        
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_text_length_validation(self):
        """Test text length validation."""
        long_text = "x" * (1000000 + 1)  # Exceeds 1MB limit
        
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisRequest(text=long_text)
        
        assert "String should have at most 1000000 characters" in str(exc_info.value)
    
    def test_source_id_validation(self):
        """Test source_id validation."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisRequest(text="test", source_id="")
        
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_options_validation(self):
        """Test options validation."""
        # Valid options
        request = SentimentAnalysisRequest(
            text="test",
            options={
                "include_confidence": True,
                "include_pii_detection": False,
                "language_code": "en"
            }
        )
        assert request.options["include_confidence"] is True
        assert request.options["include_pii_detection"] is False
        assert request.options["language_code"] == "en"
    
    def test_invalid_options_type(self):
        """Test invalid options type."""
        with pytest.raises(ValidationError):
            SentimentAnalysisRequest(text="test", options="invalid")


class TestAsyncSentimentAnalysisRequest:
    """Test AsyncSentimentAnalysisRequest model."""
    
    def test_valid_async_request(self):
        """Test valid async request creation."""
        request = AsyncSentimentAnalysisRequest(
            text="I love this product!",
            source_id="test-source",
            options={"include_confidence": True}
        )
        
        assert request.text == "I love this product!"
        assert request.source_id == "test-source"
        assert request.options == {"include_confidence": True}
    
    def test_async_text_length_validation(self):
        """Test async text length validation."""
        long_text = "x" * (1048576 + 1)  # Exceeds 1MB limit for async
        
        with pytest.raises(ValidationError) as exc_info:
            AsyncSentimentAnalysisRequest(text=long_text)
        
        assert "String should have at most 1048576 characters" in str(exc_info.value)


class TestJobStatusRequest:
    """Test JobStatusRequest model."""
    
    def test_valid_job_status_request(self):
        """Test valid job status request creation."""
        request = JobStatusRequest(job_id="test-job-123")
        
        assert request.job_id == "test-job-123"
    
    def test_empty_job_id_validation(self):
        """Test empty job_id validation."""
        with pytest.raises(ValidationError) as exc_info:
            JobStatusRequest(job_id="")
        
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_invalid_job_id_format(self):
        """Test invalid job_id format."""
        with pytest.raises(ValidationError) as exc_info:
            JobStatusRequest(job_id="invalid-job-id-format!")
        
        assert "String should match pattern" in str(exc_info.value)


class TestSentimentAnalysisResponse:
    """Test SentimentAnalysisResponse model."""
    
    def test_valid_response(self):
        """Test valid response creation."""
        response = SentimentAnalysisResponse(
            sentiment="POSITIVE",
            score=0.95,
            language_code="en",
            confidence=True,
            pii_detected=False,
            processing_time_ms=150
        )
        
        assert response.sentiment == "POSITIVE"
        assert response.score == 0.95
        assert response.language_code == "en"
        assert response.confidence is True
        assert response.pii_detected is False
        assert response.processing_time_ms == 150
    
    def test_minimal_response(self):
        """Test minimal response creation."""
        response = SentimentAnalysisResponse(
            sentiment="POSITIVE",
            score=0.95,
            processing_time_ms=150
        )
        
        assert response.sentiment == "POSITIVE"
        assert response.score == 0.95
        assert response.language_code is None
        assert response.confidence is True  # Default value
        assert response.pii_detected is False  # Default value
        assert response.processing_time_ms == 150
    
    def test_sentiment_validation(self):
        """Test sentiment validation."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisResponse(
                sentiment="INVALID",
                score=0.95,
                processing_time_ms=150
            )
        
        assert "Input should be" in str(exc_info.value)
    
    def test_score_validation(self):
        """Test score validation."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisResponse(
                sentiment="POSITIVE",
                score=1.5,  # Invalid score > 1.0
                processing_time_ms=150
            )
        
        assert "Input should be less than or equal to 1" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisResponse(
                sentiment="POSITIVE",
                score=-0.1,  # Invalid score < 0.0
                processing_time_ms=150
            )
        
        assert "Input should be greater than or equal to 0" in str(exc_info.value)


class TestAsyncJobResponse:
    """Test AsyncJobResponse model."""
    
    def test_valid_async_response(self):
        """Test valid async response creation."""
        response = AsyncJobResponse(
            job_id="test-job-123",
            status="PROCESSING",
            message="Job submitted successfully",
            estimated_completion=datetime.now(timezone.utc)
        )
        
        assert response.job_id == "test-job-123"
        assert response.status == "PROCESSING"
        assert response.message == "Job submitted successfully"
        assert isinstance(response.estimated_completion, datetime)
    
    def test_status_validation(self):
        """Test status validation."""
        with pytest.raises(ValidationError) as exc_info:
            AsyncJobResponse(
                job_id="test-job-123",
                status="INVALID_STATUS",
                message="Test message",
                estimated_completion=datetime.now(timezone.utc)
            )
        
        assert "Input should be" in str(exc_info.value)


class TestJobStatusResponse:
    """Test JobStatusResponse model."""
    
    def test_valid_job_status_response(self):
        """Test valid job status response creation."""
        response = JobStatusResponse(
            job_id="test-job-123",
            status="COMPLETED",
            result={
                "sentiment": "POSITIVE",
                "score": 0.95,
                "language_code": "en"
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert response.job_id == "test-job-123"
        assert response.status == "COMPLETED"
        assert response.result["sentiment"] == "POSITIVE"
        assert isinstance(response.created_at, datetime)
        assert isinstance(response.updated_at, datetime)
    
    def test_processing_status_response(self):
        """Test processing status response creation."""
        response = JobStatusResponse(
            job_id="test-job-123",
            status="PROCESSING",
            result=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert response.job_id == "test-job-123"
        assert response.status == "PROCESSING"
        assert response.result is None


class TestHealthResponse:
    """Test HealthResponse model."""
    
    def test_valid_health_response(self):
        """Test valid health response creation."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.now(timezone.utc)
        )
        
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert isinstance(response.timestamp, datetime)
    
    def test_health_status_validation(self):
        """Test health status validation."""
        with pytest.raises(ValidationError) as exc_info:
            HealthResponse(
                status="invalid",
                version="1.0.0",
                timestamp=datetime.now(timezone.utc)
            )
        
        assert "Input should be" in str(exc_info.value)


class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_valid_error_response(self):
        """Test valid error response creation."""
        error_response = ErrorResponse(
            error={
                "code": "VALIDATION_ERROR",
                "message": "Invalid input",
                "request_id": "test-request-id",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        assert error_response.error["code"] == "VALIDATION_ERROR"
        assert error_response.error["message"] == "Invalid input"
        assert error_response.error["request_id"] == "test-request-id"
        assert "timestamp" in error_response.error
    
    def test_error_structure_validation(self):
        """Test error structure validation."""
        with pytest.raises(ValidationError):
            ErrorResponse(error="invalid error structure")
