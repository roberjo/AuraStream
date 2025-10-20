"""Tests for update job status handler."""

import os
from unittest.mock import Mock, patch

import pytest

from src.handlers.update_job_status_handler import _update_job_status, lambda_handler


class TestUpdateJobStatusHandler:
    """Test update job status handler functionality."""

    def test_successful_job_status_update(self):
        """Test successful job status update."""
        mock_context = Mock()
        mock_context.aws_request_id = "test-request-id"

        event = {
            "job_id": "job-123-456-789",
            "status": "COMPLETED",
            "result": {"sentiment": "POSITIVE", "score": 0.95},
            "error": None,
        }

        with patch(
            "src.handlers.update_job_status_handler._update_job_status"
        ) as mock_update, patch(
            "src.handlers.update_job_status_handler.metrics"
        ) as mock_metrics:
            mock_update.return_value = True

            response = lambda_handler(event, mock_context)

            assert response["statusCode"] == 200
            assert response["job_id"] == "job-123-456-789"
            assert response["status"] == "COMPLETED"
            assert "updated_at" in response
            mock_metrics.record_business_metric.assert_called_with(
                "JobsCompleted", 1, "Count"
            )

    def test_successful_failed_job_status_update(self):
        """Test successful failed job status update."""
        mock_context = Mock()
        mock_context.aws_request_id = "test-request-id"

        event = {
            "job_id": "job-123-456-789",
            "status": "FAILED",
            "result": None,
            "error": {"error": "Processing failed"},
        }

        with patch(
            "src.handlers.update_job_status_handler._update_job_status"
        ) as mock_update, patch(
            "src.handlers.update_job_status_handler.metrics"
        ) as mock_metrics:
            mock_update.return_value = True

            response = lambda_handler(event, mock_context)

            assert response["statusCode"] == 200
            assert response["job_id"] == "job-123-456-789"
            assert response["status"] == "FAILED"
            mock_metrics.record_business_metric.assert_called_with(
                "JobsFailed", 1, "Count"
            )

    def test_successful_processing_job_status_update(self):
        """Test successful processing job status update."""
        mock_context = Mock()
        mock_context.aws_request_id = "test-request-id"

        event = {
            "job_id": "job-123-456-789",
            "status": "PROCESSING",
            "result": None,
            "error": None,
        }

        with patch(
            "src.handlers.update_job_status_handler._update_job_status"
        ) as mock_update, patch(
            "src.handlers.update_job_status_handler.metrics"
        ) as mock_metrics:
            mock_update.return_value = True

            response = lambda_handler(event, mock_context)

            assert response["statusCode"] == 200
            assert response["job_id"] == "job-123-456-789"
            assert response["status"] == "PROCESSING"
            # No business metric should be recorded for PROCESSING status
            mock_metrics.record_business_metric.assert_not_called()

    def test_missing_job_id(self):
        """Test error handling for missing job ID."""
        mock_context = Mock()
        event = {
            "status": "COMPLETED",
            "result": {"sentiment": "POSITIVE"},
        }

        with patch("src.handlers.update_job_status_handler.metrics") as mock_metrics:
            with pytest.raises(ValueError, match="Job ID is required"):
                lambda_handler(event, mock_context)

            mock_metrics.record_error.assert_called_once()

    def test_update_job_status_failure(self):
        """Test error handling when job status update fails."""
        mock_context = Mock()
        event = {
            "job_id": "job-123-456-789",
            "status": "COMPLETED",
            "result": {"sentiment": "POSITIVE"},
        }

        with patch(
            "src.handlers.update_job_status_handler._update_job_status"
        ) as mock_update, patch(
            "src.handlers.update_job_status_handler.metrics"
        ) as mock_metrics:
            mock_update.return_value = False

            with pytest.raises(ValueError, match="Failed to update job"):
                lambda_handler(event, mock_context)

            mock_metrics.record_error.assert_called_once()

    def test_default_status(self):
        """Test default status when not provided."""
        mock_context = Mock()
        event = {
            "job_id": "job-123-456-789",
            "result": {"sentiment": "POSITIVE"},
        }

        with patch(
            "src.handlers.update_job_status_handler._update_job_status"
        ) as mock_update:
            mock_update.return_value = True

            response = lambda_handler(event, mock_context)

            assert response["status"] == "PROCESSING"
            mock_update.assert_called_once_with(
                "job-123-456-789", "PROCESSING", {"sentiment": "POSITIVE"}, None
            )

    def test_update_job_status_success_with_result(self):
        """Test successful job status update with result."""
        with patch(
            "src.handlers.update_job_status_handler.aws_clients"
        ) as mock_aws, patch.dict(os.environ, {"JOB_RESULTS_TABLE": "test-table"}):
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            result = _update_job_status(
                "job-123", "COMPLETED", {"sentiment": "POSITIVE", "score": 0.95}, None
            )

            assert result is True
            mock_table.update_item.assert_called_once()

            # Verify the update expression includes result and completed_at
            call_args = mock_table.update_item.call_args
            update_expression = call_args[1]["UpdateExpression"]
            assert "#result" in update_expression
            assert "#completed_at" in update_expression

    def test_update_job_status_success_with_error(self):
        """Test successful job status update with error."""
        with patch(
            "src.handlers.update_job_status_handler.aws_clients"
        ) as mock_aws, patch.dict(os.environ, {"JOB_RESULTS_TABLE": "test-table"}):
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            result = _update_job_status(
                "job-123",
                "FAILED",
                None,
                {"error": "Processing failed", "error_type": "ValueError"},
            )

            assert result is True
            mock_table.update_item.assert_called_once()

            # Verify the update expression includes error
            call_args = mock_table.update_item.call_args
            update_expression = call_args[1]["UpdateExpression"]
            assert "#error" in update_expression

    def test_update_job_status_success_without_result_or_error(self):
        """Test successful job status update without result or error."""
        with patch(
            "src.handlers.update_job_status_handler.aws_clients"
        ) as mock_aws, patch.dict(os.environ, {"JOB_RESULTS_TABLE": "test-table"}):
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            result = _update_job_status("job-123", "PROCESSING", None, None)

            assert result is True
            mock_table.update_item.assert_called_once()

            # Verify the update expression only includes status and updated_at
            call_args = mock_table.update_item.call_args
            update_expression = call_args[1]["UpdateExpression"]
            assert "#result" not in update_expression
            assert "#error" not in update_expression
            assert "#status" in update_expression
            assert "#updated_at" in update_expression

    def test_update_job_status_error(self):
        """Test error handling in job status update."""
        with patch("src.handlers.update_job_status_handler.aws_clients") as mock_aws:
            mock_dynamodb = Mock()
            mock_dynamodb.Table.side_effect = Exception("DynamoDB error")
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            result = _update_job_status("job-123", "COMPLETED", None, None)

            assert result is False

    def test_update_job_status_with_both_result_and_error(self):
        """Test job status update with both result and error (edge case)."""
        with patch(
            "src.handlers.update_job_status_handler.aws_clients"
        ) as mock_aws, patch.dict(os.environ, {"JOB_RESULTS_TABLE": "test-table"}):
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            result = _update_job_status(
                "job-123",
                "COMPLETED",
                {"sentiment": "POSITIVE"},
                {"warning": "Minor issue"},
            )

            assert result is True
            mock_table.update_item.assert_called_once()

            # Verify the update expression includes both result and error
            call_args = mock_table.update_item.call_args
            update_expression = call_args[1]["UpdateExpression"]
            assert "#result" in update_expression
            assert "#error" in update_expression
