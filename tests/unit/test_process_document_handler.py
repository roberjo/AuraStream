"""Tests for process document handler."""

import os
from unittest.mock import Mock, patch

import pytest

from src.handlers.process_document_handler import (
    _get_document_from_s3,
    _process_large_text_with_comprehend,
    _process_with_comprehend,
    _update_job_status,
    lambda_handler,
)


class TestProcessDocumentHandler:
    """Test process document handler functionality."""

    def test_successful_document_processing(self):
        """Test successful document processing."""
        mock_context = Mock()
        mock_context.aws_request_id = "test-request-id"

        event = {
            "job_id": "job-123-456-789",
            "options": {"language_code": "en"},
        }

        with patch(
            "src.handlers.process_document_handler._get_document_from_s3"
        ) as mock_get_doc, patch(
            "src.handlers.process_document_handler._process_with_comprehend"
        ) as mock_process, patch(
            "src.handlers.process_document_handler._update_job_status"
        ) as mock_update, patch(
            "src.handlers.process_document_handler.metrics"
        ) as mock_metrics:
            mock_get_doc.return_value = "This is a test document"
            mock_process.return_value = {
                "Sentiment": "POSITIVE",
                "SentimentScore": {
                    "Positive": 0.95,
                    "Negative": 0.02,
                    "Neutral": 0.02,
                    "Mixed": 0.01,
                },
                "LanguageCode": "en",
            }
            mock_update.return_value = True

            response = lambda_handler(event, mock_context)

            assert response["statusCode"] == 200
            assert response["job_id"] == "job-123-456-789"
            assert response["status"] == "COMPLETED"
            assert "result" in response
            mock_metrics.record_sentiment_analysis.assert_called_once()

    def test_missing_job_id(self):
        """Test error handling for missing job ID."""
        mock_context = Mock()
        event = {"options": {"language_code": "en"}}

        with patch(
            "src.handlers.process_document_handler._update_job_status"
        ) as mock_update, patch(
            "src.handlers.process_document_handler.metrics"
        ) as mock_metrics:
            with pytest.raises(ValueError, match="Job ID is required"):
                lambda_handler(event, mock_context)

            mock_update.assert_called_once()
            mock_metrics.record_error.assert_called_once()

    def test_document_not_found(self):
        """Test error handling when document is not found."""
        mock_context = Mock()
        event = {
            "job_id": "job-123-456-789",
            "options": {"language_code": "en"},
        }

        with patch(
            "src.handlers.process_document_handler._get_document_from_s3"
        ) as mock_get_doc, patch(
            "src.handlers.process_document_handler._update_job_status"
        ) as mock_update, patch(
            "src.handlers.process_document_handler.metrics"
        ) as mock_metrics:
            mock_get_doc.return_value = None

            with pytest.raises(ValueError, match="Document not found"):
                lambda_handler(event, mock_context)

            mock_update.assert_called_once()
            mock_metrics.record_error.assert_called_once()

    def test_get_document_from_s3_success(self):
        """Test successful document retrieval from S3."""
        with patch(
            "src.handlers.process_document_handler.aws_clients"
        ) as mock_aws, patch.dict(os.environ, {"DOCUMENTS_BUCKET": "test-bucket"}):
            mock_s3 = Mock()
            mock_response = {"Body": Mock()}
            mock_response["Body"].read.return_value = b"Test document content"
            mock_s3.get_object.return_value = mock_response
            mock_aws.get_s3_client.return_value = mock_s3

            result = _get_document_from_s3("job-123")

            assert result == "Test document content"
            mock_s3.get_object.assert_called_once_with(
                Bucket="test-bucket", Key="documents/job-123.txt"
            )

    def test_get_document_from_s3_error(self):
        """Test error handling in document retrieval from S3."""
        with patch("src.handlers.process_document_handler.aws_clients") as mock_aws:
            mock_s3 = Mock()
            mock_s3.get_object.side_effect = Exception("S3 error")
            mock_aws.get_s3_client.return_value = mock_s3

            result = _get_document_from_s3("job-123")

            assert result is None

    def test_process_with_comprehend_small_text(self):
        """Test processing small text with Comprehend."""
        with patch("src.handlers.process_document_handler.aws_clients") as mock_aws:
            mock_comprehend = Mock()
            mock_comprehend.detect_sentiment.return_value = {
                "Sentiment": "POSITIVE",
                "SentimentScore": {
                    "Positive": 0.95,
                    "Negative": 0.02,
                    "Neutral": 0.02,
                    "Mixed": 0.01,
                },
                "LanguageCode": "en",
            }
            mock_aws.get_comprehend_client.return_value = mock_comprehend

            result = _process_with_comprehend("Short text", {"language_code": "en"})

            assert result["Sentiment"] == "POSITIVE"
            assert result["ProcessingMethod"] == "real-time"
            assert result["TextLength"] == 10
            mock_comprehend.detect_sentiment.assert_called_once()

    def test_process_with_comprehend_large_text(self):
        """Test processing large text with Comprehend batch processing."""
        large_text = "x" * 6000  # Larger than 5000 characters

        with patch(
            "src.handlers.process_document_handler._process_large_text_with_comprehend"
        ) as mock_batch:
            mock_batch.return_value = {
                "Sentiment": "PROCESSING",
                "ProcessingMethod": "batch",
                "BatchJobId": "batch-123",
            }

            result = _process_with_comprehend(large_text, {"language_code": "en"})

            assert result["Sentiment"] == "PROCESSING"
            assert result["ProcessingMethod"] == "batch"
            mock_batch.assert_called_once_with(large_text, {"language_code": "en"})

    def test_process_with_comprehend_error(self):
        """Test error handling in Comprehend processing."""
        with patch("src.handlers.process_document_handler.aws_clients") as mock_aws:
            mock_comprehend = Mock()
            mock_comprehend.detect_sentiment.side_effect = Exception("Comprehend error")
            mock_aws.get_comprehend_client.return_value = mock_comprehend

            with pytest.raises(Exception, match="Comprehend error"):
                _process_with_comprehend("Test text", {"language_code": "en"})

    def test_process_large_text_with_comprehend(self):
        """Test batch processing of large text."""
        with patch(
            "src.handlers.process_document_handler.aws_clients"
        ) as mock_aws, patch("uuid.uuid4") as mock_uuid, patch.dict(
            os.environ,
            {
                "DOCUMENTS_BUCKET": "test-bucket",
                "COMPREHEND_ROLE_ARN": "arn:aws:iam::123456789012:role/ComprehendRole",
            },
        ):
            mock_comprehend = Mock()
            mock_s3 = Mock()
            mock_uuid.return_value = "test-uuid-123"
            mock_comprehend.start_sentiment_detection_job.return_value = {
                "JobId": "batch-job-123"
            }
            mock_aws.get_comprehend_client.return_value = mock_comprehend
            mock_aws.get_s3_client.return_value = mock_s3

            result = _process_large_text_with_comprehend(
                "Large text content", {"language_code": "en"}
            )

            assert result["Sentiment"] == "PROCESSING"
            assert result["ProcessingMethod"] == "batch"
            assert result["BatchJobId"] == "batch-job-123"
            mock_s3.put_object.assert_called_once()
            mock_comprehend.start_sentiment_detection_job.assert_called_once()

    def test_process_large_text_with_comprehend_error(self):
        """Test error handling in batch processing."""
        with patch("src.handlers.process_document_handler.aws_clients") as mock_aws:
            mock_comprehend = Mock()
            mock_comprehend.start_sentiment_detection_job.side_effect = Exception(
                "Batch error"
            )
            mock_aws.get_comprehend_client.return_value = mock_comprehend

            with pytest.raises(Exception, match="Batch error"):
                _process_large_text_with_comprehend(
                    "Large text", {"language_code": "en"}
                )

    def test_update_job_status_success(self):
        """Test successful job status update."""
        with patch(
            "src.handlers.process_document_handler.aws_clients"
        ) as mock_aws, patch.dict(os.environ, {"JOB_RESULTS_TABLE": "test-table"}):
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            result = _update_job_status(
                "job-123", "COMPLETED", {"sentiment": "POSITIVE"}, None
            )

            assert result is True
            mock_table.update_item.assert_called_once()

    def test_update_job_status_with_error(self):
        """Test job status update with error information."""
        with patch(
            "src.handlers.process_document_handler.aws_clients"
        ) as mock_aws, patch.dict(os.environ, {"JOB_RESULTS_TABLE": "test-table"}):
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            result = _update_job_status(
                "job-123", "FAILED", None, {"error": "Processing failed"}
            )

            assert result is True
            mock_table.update_item.assert_called_once()

    def test_update_job_status_error(self):
        """Test error handling in job status update."""
        with patch("src.handlers.process_document_handler.aws_clients") as mock_aws:
            mock_dynamodb = Mock()
            mock_dynamodb.Table.side_effect = Exception("DynamoDB error")
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            result = _update_job_status("job-123", "COMPLETED", None, None)

            assert result is False
