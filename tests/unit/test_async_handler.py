"""Unit tests for async handler."""

import json
from unittest.mock import patch

from src.handlers.async_handler import lambda_handler


class TestAsyncHandler:
    """Test suite for async handler."""

    def test_successful_async_analysis(self, api_event, lambda_context):
        """Test successful async sentiment analysis."""
        # Mock the async event
        async_event = {
            "httpMethod": "POST",
            "path": "/analyze/async",
            "body": json.dumps(
                {
                    "text": "This is a longer text for async processing.",
                    "source_id": "test-source-123",
                    "options": {"language_code": "en", "include_confidence": True},
                }
            ),
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

        with (
            patch("src.handlers.async_handler._store_job") as mock_store_job,
            patch("src.handlers.async_handler._store_document") as mock_store_document,
            patch("src.handlers.async_handler._start_step_function") as mock_start_step,
        ):
            mock_store_job.return_value = True
            mock_store_document.return_value = True
            mock_start_step.return_value = True

            response = lambda_handler(async_event, lambda_context)

            assert response["statusCode"] == 202
            body = json.loads(response["body"])
            assert body["status"] == "PROCESSING"
            assert "job_id" in body
            assert "estimated_completion" in body
            assert body["message"] == "Job submitted successfully"

    def test_invalid_text_validation(self, lambda_context):
        """Test validation of invalid text input."""
        event = {
            "httpMethod": "POST",
            "path": "/analyze/async",
            "body": '{"text": ""}',
            "headers": {"Content-Type": "application/json"},
        }

        response = lambda_handler(event, lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"

    def test_text_length_validation(self, lambda_context):
        """Test validation of text length limits."""
        long_text = "x" * 1048577  # Exceeds 1MB limit
        event = {
            "httpMethod": "POST",
            "path": "/analyze/async",
            "body": f'{{"text": "{long_text}"}}',
            "headers": {"Content-Type": "application/json"},
        }

        response = lambda_handler(event, lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert (
            "ensure this value has at most 1048576 characters" in body["error"]["message"]
        )

    def test_security_validation(self, lambda_context):
        """Test security validation for malicious input."""
        malicious_text = "'; DROP TABLE users; --"
        event = {
            "httpMethod": "POST",
            "path": "/analyze/async",
            "body": f'{{"text": "{malicious_text}"}}',
            "headers": {"Content-Type": "application/json"},
        }

        response = lambda_handler(event, lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "malicious content" in body["error"]["message"]

    def test_job_storage_failure(self, lambda_context):
        """Test handling of job storage failure."""
        async_event = {
            "httpMethod": "POST",
            "path": "/analyze/async",
            "body": json.dumps(
                {"text": "This is a test text.", "source_id": "test-source-123"}
            ),
            "headers": {"Content-Type": "application/json"},
        }

        with patch("src.handlers.async_handler._store_job") as mock_store_job:
            mock_store_job.return_value = False

            response = lambda_handler(async_event, lambda_context)

            assert response["statusCode"] == 500
            body = json.loads(response["body"])
            assert body["error"]["code"] == "INTERNAL_ERROR"
            assert "Failed to store job information" in body["error"]["message"]

    def test_document_storage_failure(self, lambda_context):
        """Test handling of document storage failure."""
        async_event = {
            "httpMethod": "POST",
            "path": "/analyze/async",
            "body": json.dumps(
                {"text": "This is a test text.", "source_id": "test-source-123"}
            ),
            "headers": {"Content-Type": "application/json"},
        }

        with (
            patch("src.handlers.async_handler._store_job") as mock_store_job,
            patch("src.handlers.async_handler._store_document") as mock_store_document,
        ):
            mock_store_job.return_value = True
            mock_store_document.return_value = False

            response = lambda_handler(async_event, lambda_context)

            assert response["statusCode"] == 500
            body = json.loads(response["body"])
            assert body["error"]["code"] == "INTERNAL_ERROR"
            assert "Failed to store document" in body["error"]["message"]

    def test_step_function_failure(self, lambda_context):
        """Test handling of Step Functions failure."""
        async_event = {
            "httpMethod": "POST",
            "path": "/analyze/async",
            "body": json.dumps(
                {"text": "This is a test text.", "source_id": "test-source-123"}
            ),
            "headers": {"Content-Type": "application/json"},
        }

        with (
            patch("src.handlers.async_handler._store_job") as mock_store_job,
            patch("src.handlers.async_handler._store_document") as mock_store_document,
            patch("src.handlers.async_handler._start_step_function") as mock_start_step,
        ):
            mock_store_job.return_value = True
            mock_store_document.return_value = True
            mock_start_step.return_value = False

            response = lambda_handler(async_event, lambda_context)

            assert response["statusCode"] == 500
            body = json.loads(response["body"])
            assert body["error"]["code"] == "INTERNAL_ERROR"
            assert "Failed to start processing" in body["error"]["message"]

    def test_error_handling(self, lambda_context):
        """Test error handling for internal errors."""
        async_event = {
            "httpMethod": "POST",
            "path": "/analyze/async",
            "body": "invalid json",
            "headers": {"Content-Type": "application/json"},
        }

        response = lambda_handler(async_event, lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"

    def test_estimated_completion_calculation(self):
        """Test estimated completion time calculation."""
        from src.handlers.async_handler import _calculate_estimated_completion

        # Test with short text
        short_text = "Short text"
        completion_time = _calculate_estimated_completion(short_text)

        # Should be approximately 30 seconds + small amount for text length
        assert completion_time is not None

        # Test with long text
        long_text = "x" * 10000
        completion_time_long = _calculate_estimated_completion(long_text)

        # Should be longer than short text
        assert completion_time_long > completion_time
