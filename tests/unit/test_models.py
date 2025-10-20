"""Unit tests for Pydantic models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models.request_models import (
    AsyncSentimentAnalysisRequest,
    JobStatusRequest,
    SentimentAnalysisRequest,
)
from src.models.response_models import (
    AsyncJobResponse,
    ErrorResponse,
    HealthResponse,
    JobStatusResponse,
    SentimentAnalysisResponse,
)


class TestSentimentAnalysisRequest:
    """Test SentimentAnalysisRequest model."""

    def test_valid_request(self):
        """Test valid request creation."""
        request = SentimentAnalysisRequest(
            text="I love this product!",
            options={
                "language_code": "en",
                "include_confidence": True,
                "include_pii_detection": False,
            },
        )
        assert request.text == "I love this product!"
        assert request.options["language_code"] == "en"
        assert request.options["include_confidence"] is True
        assert request.options["include_pii_detection"] is False

    def test_minimal_request(self):
        """Test minimal request creation."""
        request = SentimentAnalysisRequest(text="Hello world!")
        assert request.text == "Hello world!"
        assert request.options is None

    def test_empty_text_validation(self):
        """Test empty text validation."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisRequest(text="")
        assert "Text cannot be empty" in str(exc_info.value)

    def test_whitespace_only_text_validation(self):
        """Test whitespace-only text validation."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisRequest(text="   \n\t   ")
        assert "Text cannot be empty" in str(exc_info.value)

    def test_text_length_validation(self):
        """Test text length validation."""
        long_text = "x" * 5001  # Exceeds 5000 character limit
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisRequest(text=long_text)
        # Check for either Pydantic v1 or v2 error message format
        error_str = str(exc_info.value)
        assert (
            "String should have at most 5000 characters" in error_str
            or "ensure this value has at most 5000 characters" in error_str
        )

    def test_options_validation(self):
        """Test options validation."""
        request = SentimentAnalysisRequest(
            text="Test text",
            options={
                "language_code": "en",
                "include_confidence": True,
                "include_pii_detection": False,
                "custom_option": "value",
            },
        )
        assert request.options["language_code"] == "en"
        assert request.options["include_confidence"] is True
        assert request.options["include_pii_detection"] is False
        assert request.options["custom_option"] == "value"

    def test_invalid_options_type(self):
        """Test invalid options type."""
        with pytest.raises(ValidationError):
            SentimentAnalysisRequest(text="Test text", options="invalid")


class TestAsyncSentimentAnalysisRequest:
    """Test AsyncSentimentAnalysisRequest model."""

    def test_valid_async_request(self):
        """Test valid async request creation."""
        request = AsyncSentimentAnalysisRequest(
            text="I love this product!",
            source_id="test-source-123",
            options={"language_code": "en", "include_confidence": True},
        )
        assert request.text == "I love this product!"
        assert request.source_id == "test-source-123"
        assert request.options["language_code"] == "en"

    def test_async_text_length_validation(self):
        """Test async text length validation."""
        long_text = "x" * 1048577  # Exceeds 1MB limit
        with pytest.raises(ValidationError) as exc_info:
            AsyncSentimentAnalysisRequest(text=long_text, source_id="test")
        # Check for either Pydantic v1 or v2 error message format
        error_str = str(exc_info.value)
        assert (
            "String should have at most 1048576 characters" in error_str
            or "ensure this value has at most 1048576 characters" in error_str
        )

    def test_source_id_validation(self):
        """Test source_id validation."""
        request = AsyncSentimentAnalysisRequest(
            text="Test text", source_id="valid-source-id-123"
        )
        assert request.source_id == "valid-source-id-123"

    def test_optional_source_id(self):
        """Test optional source_id."""
        request = AsyncSentimentAnalysisRequest(text="Test text")
        assert request.source_id is None


class TestJobStatusRequest:
    """Test JobStatusRequest model."""

    def test_valid_job_status_request(self):
        """Test valid job status request creation."""
        request = JobStatusRequest(job_id="job-123-456-789")
        assert request.job_id == "job-123-456-789"

    def test_empty_job_id_validation(self):
        """Test empty job_id validation."""
        with pytest.raises(ValidationError) as exc_info:
            JobStatusRequest(job_id="")
        assert "Job ID cannot be empty" in str(exc_info.value)

    def test_invalid_job_id_format(self):
        """Test invalid job_id format validation."""
        with pytest.raises(ValidationError) as exc_info:
            JobStatusRequest(job_id="invalid-format")
        assert "Invalid job ID format" in str(exc_info.value)


class TestSentimentAnalysisResponse:
    """Test SentimentAnalysisResponse model."""

    def test_valid_response(self):
        """Test valid response creation."""
        response = SentimentAnalysisResponse(
            sentiment="POSITIVE",
            score=0.95,
            language_code="en",
            confidence=1.0,
            pii_detected=False,
            processing_time_ms=150,
        )
        assert response.sentiment == "POSITIVE"
        assert response.score == 0.95
        assert response.language_code == "en"
        assert response.confidence == 1.0
        assert response.pii_detected is False
        assert response.processing_time_ms == 150

    def test_minimal_response(self):
        """Test minimal response creation."""
        response = SentimentAnalysisResponse(
            sentiment="POSITIVE", score=0.95, processing_time_ms=150
        )
        assert response.sentiment == "POSITIVE"
        assert response.score == 0.95
        assert response.language_code is None
        assert response.confidence is None
        assert response.pii_detected is None

    def test_sentiment_validation(self):
        """Test sentiment validation."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisResponse(
                sentiment="INVALID", score=0.95, processing_time_ms=150
            )
        assert "Sentiment must be one of" in str(exc_info.value)

    def test_score_validation(self):
        """Test score validation."""
        with pytest.raises(ValidationError):
            SentimentAnalysisResponse(
                sentiment="POSITIVE",
                score=1.5,  # Invalid score > 1.0
                processing_time_ms=150,
            )


class TestAsyncJobResponse:
    """Test AsyncJobResponse model."""

    def test_valid_async_response(self):
        """Test valid async response creation."""
        response = AsyncJobResponse(
            job_id="job-123-456-789",
            status="SUBMITTED",
            estimated_completion="2023-12-25T10:30:00Z",
        )
        assert response.job_id == "job-123-456-789"
        assert response.status == "SUBMITTED"
        assert response.estimated_completion == "2023-12-25T10:30:00Z"

    def test_status_validation(self):
        """Test status validation."""
        with pytest.raises(ValidationError) as exc_info:
            AsyncJobResponse(job_id="job-123", status="INVALID_STATUS")
        assert "Status must be one of" in str(exc_info.value)


class TestJobStatusResponse:
    """Test JobStatusResponse model."""

    def test_valid_job_status_response(self):
        """Test valid job status response creation."""
        result = SentimentAnalysisResponse(
            sentiment="POSITIVE", score=0.95, processing_time_ms=150
        )
        response = JobStatusResponse(
            job_id="job-123-456-789", status="COMPLETED", result=result
        )
        assert response.job_id == "job-123-456-789"
        assert response.status == "COMPLETED"
        assert response.result.sentiment == "POSITIVE"

    def test_processing_status_response(self):
        """Test processing status response creation."""
        response = JobStatusResponse(
            job_id="job-123-456-789", status="PROCESSING", progress=50
        )
        assert response.job_id == "job-123-456-789"
        assert response.status == "PROCESSING"
        assert response.progress == 50
        assert response.result is None


class TestHealthResponse:
    """Test HealthResponse model."""

    def test_valid_health_response(self):
        """Test valid health response creation."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.now(timezone.utc),
            components={
                "database": "healthy",
                "cache": "healthy",
                "external_services": "healthy",
            },
        )
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.components["database"] == "healthy"

    def test_health_status_validation(self):
        """Test health status validation."""
        with pytest.raises(ValidationError) as exc_info:
            HealthResponse(
                status="invalid",
                version="1.0.0",
                timestamp=datetime.now(timezone.utc),
                components={},
            )
        assert "Status must be one of" in str(exc_info.value)


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_valid_error_response(self):
        """Test valid error response creation."""
        response = ErrorResponse(
            error="VALIDATION_ERROR",
            message="Invalid input provided",
            details={"field": "text", "issue": "too long"},
        )
        assert response.error == "VALIDATION_ERROR"
        assert response.message == "Invalid input provided"
        assert response.details["field"] == "text"

    def test_error_structure_validation(self):
        """Test error response structure validation."""
        response = ErrorResponse(
            error="INTERNAL_ERROR", message="An unexpected error occurred"
        )
        assert response.error == "INTERNAL_ERROR"
        assert response.message == "An unexpected error occurred"
        assert response.details is None
