"""Unit tests for status handler."""

import json
from unittest.mock import Mock, patch

from src.handlers.status_handler import lambda_handler


class TestStatusHandler:
    """Test suite for status handler."""

    def test_successful_status_retrieval(self, lambda_context):
        """Test successful job status retrieval."""
        event = {
            "httpMethod": "GET",
            "path": "/status/123e4567-e89b-12d3-a456-426614174000",
            "pathParameters": {"job_id": "123e4567-e89b-12d3-a456-426614174000"},
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

        mock_job_data = {
            "job_id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "COMPLETED",
            "created_at": "2024-01-01T00:00:00Z",
            "completed_at": "2024-01-01T00:01:00Z",
            "result": {"sentiment": "POSITIVE", "score": 0.95},
            "source_id": "test-source-123",
        }

        with patch("src.handlers.status_handler._get_job_status") as mock_get_job:
            mock_get_job.return_value = mock_job_data

            response = lambda_handler(event, lambda_context)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["job_id"] == "123e4567-e89b-12d3-a456-426614174000"
            assert body["status"] == "COMPLETED"
            assert body["result"]["sentiment"] == "POSITIVE"
            assert body["source_id"] == "test-source-123"

    def test_job_not_found(self, lambda_context):
        """Test handling of non-existent job."""
        event = {
            "httpMethod": "GET",
            "path": "/status/123e4567-e89b-12d3-a456-426614174000",
            "pathParameters": {"job_id": "123e4567-e89b-12d3-a456-426614174000"},
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

        with patch("src.handlers.status_handler._get_job_status") as mock_get_job:
            mock_get_job.return_value = None

            response = lambda_handler(event, lambda_context)

            assert response["statusCode"] == 404
            body = json.loads(response["body"])
            assert body["error"]["code"] == "NOT_FOUND"
            assert "Job not found" in body["error"]["message"]

    def test_missing_job_id(self, lambda_context):
        """Test handling of missing job ID."""
        event = {
            "httpMethod": "GET",
            "path": "/status/",
            "pathParameters": {},
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

        response = lambda_handler(event, lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "Job ID is required" in body["error"]["message"]

    def test_invalid_job_id_format(self, lambda_context):
        """Test handling of invalid job ID format."""
        event = {
            "httpMethod": "GET",
            "path": "/status/invalid-job-id",
            "pathParameters": {"job_id": "invalid-job-id"},
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

        response = lambda_handler(event, lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "Invalid job ID format" in body["error"]["message"]

    def test_processing_status(self, lambda_context):
        """Test handling of processing status."""
        event = {
            "httpMethod": "GET",
            "path": "/status/123e4567-e89b-12d3-a456-426614174000",
            "pathParameters": {"job_id": "123e4567-e89b-12d3-a456-426614174000"},
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

        mock_job_data = {
            "job_id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "PROCESSING",
            "created_at": "2024-01-01T00:00:00Z",
            "source_id": "test-source-123",
        }

        with patch("src.handlers.status_handler._get_job_status") as mock_get_job:
            mock_get_job.return_value = mock_job_data

            response = lambda_handler(event, lambda_context)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["status"] == "PROCESSING"
            assert body["completed_at"] is None
            assert body["result"] is None

    def test_failed_status(self, lambda_context):
        """Test handling of failed status."""
        event = {
            "httpMethod": "GET",
            "path": "/status/123e4567-e89b-12d3-a456-426614174000",
            "pathParameters": {"job_id": "123e4567-e89b-12d3-a456-426614174000"},
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

        mock_job_data = {
            "job_id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "FAILED",
            "created_at": "2024-01-01T00:00:00Z",
            "completed_at": "2024-01-01T00:01:00Z",
            "error": {"error": "Processing failed", "error_type": "ProcessingError"},
            "source_id": "test-source-123",
        }

        with patch("src.handlers.status_handler._get_job_status") as mock_get_job:
            mock_get_job.return_value = mock_job_data

            response = lambda_handler(event, lambda_context)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["status"] == "FAILED"
            assert body["error"]["error"] == "Processing failed"
            assert body["result"] is None

    def test_error_handling(self, lambda_context):
        """Test error handling for internal errors."""
        event = {
            "httpMethod": "GET",
            "path": "/status/123e4567-e89b-12d3-a456-426614174000",
            "pathParameters": {"job_id": "123e4567-e89b-12d3-a456-426614174000"},
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

        with patch("src.handlers.status_handler._get_job_status") as mock_get_job:
            mock_get_job.side_effect = Exception("Database error")

            response = lambda_handler(event, lambda_context)

            assert response["statusCode"] == 500
            body = json.loads(response["body"])
            assert body["error"]["code"] == "INTERNAL_ERROR"
            assert "An internal error occurred" in body["message"]

    def test_get_job_status_function(self):
        """Test _get_job_status function."""
        from src.handlers.status_handler import _get_job_status

        # Test with valid job ID
        with patch("src.handlers.status_handler.aws_clients") as mock_aws_clients:
            mock_table = Mock()
            mock_table.get_item.return_value = {
                "Item": {"job_id": "test-job-id", "status": "COMPLETED"}
            }
            mock_aws_clients.get_dynamodb_resource.return_value.Table.return_value = (
                mock_table
            )

            result = _get_job_status("test-job-id")
            assert result is not None
            assert result["job_id"] == "test-job-id"
            assert result["status"] == "COMPLETED"

        # Test with non-existent job
        with patch("src.handlers.status_handler.aws_clients") as mock_aws_clients:
            mock_table = Mock()
            mock_table.get_item.return_value = {}
            mock_aws_clients.get_dynamodb_resource.return_value.Table.return_value = (
                mock_table
            )

            result = _get_job_status("non-existent-job")
            assert result is None

        # Test with error
        with patch("src.handlers.status_handler.aws_clients") as mock_aws_clients:
            mock_aws_clients.get_dynamodb_resource.side_effect = Exception(
                "Database error"
            )

            result = _get_job_status("test-job-id")
            assert result is None
