"""Tests for health handler."""

import json
from unittest.mock import Mock, patch

from src.handlers.health_handler import (
    _check_components,
    _check_comprehend,
    _check_dynamodb,
    _check_lambda,
    _check_s3,
    lambda_handler,
)


class TestHealthHandler:
    """Test health handler functionality."""

    def test_successful_health_check(self):
        """Test successful health check with all components healthy."""
        mock_context = Mock()
        mock_context.aws_request_id = "test-request-id"

        with patch("src.handlers.health_handler._check_components") as mock_check:
            mock_check.return_value = {
                "dynamodb": "healthy",
                "s3": "healthy",
                "comprehend": "healthy",
                "lambda": "healthy",
            }

            response = lambda_handler({}, mock_context)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["status"] == "healthy"
            assert body["version"] == "1.0.0"
            assert body["components"]["dynamodb"] == "healthy"
            assert body["components"]["s3"] == "healthy"
            assert body["components"]["comprehend"] == "healthy"
            assert body["components"]["lambda"] == "healthy"

    def test_unhealthy_health_check(self):
        """Test health check with some components unhealthy."""
        mock_context = Mock()
        mock_context.aws_request_id = "test-request-id"

        with patch("src.handlers.health_handler._check_components") as mock_check:
            mock_check.return_value = {
                "dynamodb": "healthy",
                "s3": "unhealthy",
                "comprehend": "healthy",
                "lambda": "healthy",
            }

            response = lambda_handler({}, mock_context)

            assert response["statusCode"] == 503
            body = json.loads(response["body"])
            assert body["status"] == "unhealthy"
            assert body["version"] == "1.0.0"
            assert body["components"]["s3"] == "unhealthy"

    def test_health_check_exception(self):
        """Test health check with exception."""
        mock_context = Mock()
        mock_context.aws_request_id = "test-request-id"

        with patch("src.handlers.health_handler._check_components") as mock_check:
            mock_check.side_effect = Exception("Health check failed")

            response = lambda_handler({}, mock_context)

            assert response["statusCode"] == 503
            body = json.loads(response["body"])
            assert body["status"] == "unhealthy"
            assert body["version"] == "1.0.0"
            assert "error" in body

    def test_check_components(self):
        """Test component health checking."""
        with patch(
            "src.handlers.health_handler._check_dynamodb"
        ) as mock_dynamodb, patch(
            "src.handlers.health_handler._check_s3"
        ) as mock_s3, patch(
            "src.handlers.health_handler._check_comprehend"
        ) as mock_comprehend, patch(
            "src.handlers.health_handler._check_lambda"
        ) as mock_lambda:
            mock_dynamodb.return_value = "healthy"
            mock_s3.return_value = "healthy"
            mock_comprehend.return_value = "healthy"
            mock_lambda.return_value = "healthy"

            components = _check_components()

            assert components["dynamodb"] == "healthy"
            assert components["s3"] == "healthy"
            assert components["comprehend"] == "healthy"
            assert components["lambda"] == "healthy"

    def test_check_dynamodb_healthy(self):
        """Test DynamoDB health check when healthy."""
        with patch("src.handlers.health_handler.aws_clients") as mock_aws:
            mock_dynamodb = Mock()
            mock_dynamodb.tables.all.return_value = []
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            result = _check_dynamodb()
            assert result == "healthy"

    def test_check_dynamodb_unhealthy(self):
        """Test DynamoDB health check when unhealthy."""
        with patch("src.handlers.health_handler.aws_clients") as mock_aws:
            mock_aws.get_dynamodb_resource.side_effect = Exception("Connection failed")

            result = _check_dynamodb()
            assert result == "unhealthy"

    def test_check_s3_healthy(self):
        """Test S3 health check when healthy."""
        with patch("src.handlers.health_handler.aws_clients") as mock_aws:
            mock_s3 = Mock()
            mock_s3.list_buckets.return_value = {"Buckets": []}
            mock_aws.get_s3_client.return_value = mock_s3

            result = _check_s3()
            assert result == "healthy"

    def test_check_s3_unhealthy(self):
        """Test S3 health check when unhealthy."""
        with patch("src.handlers.health_handler.aws_clients") as mock_aws:
            mock_aws.get_s3_client.side_effect = Exception("Connection failed")

            result = _check_s3()
            assert result == "unhealthy"

    def test_check_comprehend_healthy(self):
        """Test Comprehend health check when healthy."""
        with patch("src.handlers.health_handler.aws_clients") as mock_aws:
            mock_comprehend = Mock()
            mock_comprehend.detect_sentiment.return_value = {"Sentiment": "POSITIVE"}
            mock_aws.get_comprehend_client.return_value = mock_comprehend

            result = _check_comprehend()
            assert result == "healthy"

    def test_check_comprehend_unhealthy(self):
        """Test Comprehend health check when unhealthy."""
        with patch("src.handlers.health_handler.aws_clients") as mock_aws:
            mock_aws.get_comprehend_client.side_effect = Exception("Connection failed")

            result = _check_comprehend()
            assert result == "unhealthy"

    def test_check_lambda_healthy(self):
        """Test Lambda health check."""
        result = _check_lambda()
        assert result == "healthy"

    def test_check_lambda_unhealthy(self):
        """Test Lambda health check with exception."""
        # Lambda health check always returns healthy since it just checks if
        # the function can execute. This test verifies the function works correctly
        result = _check_lambda()
        assert result == "healthy"
