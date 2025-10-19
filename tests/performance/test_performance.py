"""Performance tests for AuraStream API."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import pytest

from src.handlers.async_handler import lambda_handler as async_handler
from src.handlers.sync_handler import lambda_handler as sync_handler


class TestPerformance:
    """Performance tests for API endpoints."""

    @pytest.fixture
    def lambda_context(self):
        """Sample Lambda context."""
        context = Mock()
        context.aws_request_id = "test-request-id"
        context.function_name = "test-function"
        context.function_version = "1"
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:test"
        )
        context.memory_limit_in_mb = 512
        context.remaining_time_in_millis = lambda: 30000
        return context

    @pytest.fixture
    def sync_event(self):
        """Sample sync API event."""
        return {
            "httpMethod": "POST",
            "path": "/analyze/sync",
            "body": '{"text": "I love this product!"}',
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

    @pytest.fixture
    def async_event(self):
        """Sample async API event."""
        return {
            "httpMethod": "POST",
            "path": "/analyze/async",
            "body": '{"text": "I love this product!", "source_id": "test-source"}',
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

    @pytest.mark.performance
    @pytest.mark.slow
    def test_sync_handler_response_time(self, sync_event, lambda_context):
        """Test sync handler response time under normal load."""
        with patch("src.handlers.sync_handler._analyze_sentiment") as mock_analyze:
            mock_analyze.return_value = {
                "Sentiment": "POSITIVE",
                "SentimentScore": {
                    "Positive": 0.95,
                    "Negative": 0.02,
                    "Neutral": 0.02,
                    "Mixed": 0.01,
                },
                "LanguageCode": "en",
            }

            with patch("src.handlers.sync_handler.SentimentCache") as mock_cache:
                mock_cache.return_value.get_cached_result.return_value = None
                mock_cache.return_value.store_result.return_value = True

                with patch("src.handlers.sync_handler.PIIDetector") as mock_pii:
                    mock_pii.return_value.detect_pii.return_value = {
                        "pii_detected": False
                    }

                    # Measure response time
                    start_time = time.time()
                    response = sync_handler(sync_event, lambda_context)
                    end_time = time.time()

                    response_time = (
                        end_time - start_time
                    ) * 1000  # Convert to milliseconds

                    assert response["statusCode"] == 200
                    assert response_time < 1000  # Should respond within 1 second

    @pytest.mark.performance
    @pytest.mark.slow
    def test_sync_handler_concurrent_requests(self, lambda_context):
        """Test sync handler performance under concurrent load."""

        def make_request():
            event = {
                "httpMethod": "POST",
                "path": "/analyze/sync",
                "body": json.dumps({"text": f"Test text {time.time()}"}),
                "headers": {
                    "Content-Type": "application/json",
                    "X-API-Key": "test-api-key",
                },
                "requestContext": {"requestId": f"test-request-{time.time()}"},
            }

            with patch("src.handlers.sync_handler._analyze_sentiment") as mock_analyze:
                mock_analyze.return_value = {
                    "Sentiment": "POSITIVE",
                    "SentimentScore": {
                        "Positive": 0.95,
                        "Negative": 0.02,
                        "Neutral": 0.02,
                        "Mixed": 0.01,
                    },
                    "LanguageCode": "en",
                }

                with patch("src.handlers.sync_handler.SentimentCache") as mock_cache:
                    mock_cache.return_value.get_cached_result.return_value = None
                    mock_cache.return_value.store_result.return_value = True

                    with patch("src.handlers.sync_handler.PIIDetector") as mock_pii:
                        mock_pii.return_value.detect_pii.return_value = {
                            "pii_detected": False
                        }

                        start_time = time.time()
                        response = sync_handler(event, lambda_context)
                        end_time = time.time()

                        return {
                            "status_code": response["statusCode"],
                            "response_time": (end_time - start_time) * 1000,
                        }

        # Run 10 concurrent requests
        num_requests = 10
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in futures]

        # Analyze results
        successful_requests = [r for r in results if r["status_code"] == 200]
        response_times = [r["response_time"] for r in successful_requests]

        assert len(successful_requests) == num_requests
        assert (
            max(response_times) < 2000
        )  # All requests should complete within 2 seconds
        assert (
            sum(response_times) / len(response_times) < 1000
        )  # Average should be under 1 second

    @pytest.mark.performance
    @pytest.mark.slow
    def test_sync_handler_large_text_performance(self, lambda_context):
        """Test sync handler performance with large text."""
        # Create large text (close to limit)
        large_text = "This is a test sentence. " * 40000  # ~1MB

        event = {
            "httpMethod": "POST",
            "path": "/analyze/sync",
            "body": json.dumps({"text": large_text}),
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

        with patch("src.handlers.sync_handler._analyze_sentiment") as mock_analyze:
            mock_analyze.return_value = {
                "Sentiment": "POSITIVE",
                "SentimentScore": {
                    "Positive": 0.95,
                    "Negative": 0.02,
                    "Neutral": 0.02,
                    "Mixed": 0.01,
                },
                "LanguageCode": "en",
            }

            with patch("src.handlers.sync_handler.SentimentCache") as mock_cache:
                mock_cache.return_value.get_cached_result.return_value = None
                mock_cache.return_value.store_result.return_value = True

                with patch("src.handlers.sync_handler.PIIDetector") as mock_pii:
                    mock_pii.return_value.detect_pii.return_value = {
                        "pii_detected": False
                    }

                    start_time = time.time()
                    response = sync_handler(event, lambda_context)
                    end_time = time.time()

                    response_time = (end_time - start_time) * 1000

                    assert response["statusCode"] == 200
                    assert (
                        response_time < 5000
                    )  # Should handle large text within 5 seconds

    @pytest.mark.performance
    @pytest.mark.slow
    def test_async_handler_response_time(self, async_event, lambda_context):
        """Test async handler response time."""
        with patch("src.handlers.async_handler._store_job") as mock_store_job:
            mock_store_job.return_value = True

            with patch("src.handlers.async_handler._store_document") as mock_store_doc:
                mock_store_doc.return_value = True

                with patch(
                    "src.handlers.async_handler._start_step_function"
                ) as mock_start_sf:
                    mock_start_sf.return_value = True

                    start_time = time.time()
                    response = async_handler(async_event, lambda_context)
                    end_time = time.time()

                    response_time = (end_time - start_time) * 1000

                    assert response["statusCode"] == 202
                    assert response_time < 2000  # Should respond within 2 seconds

    @pytest.mark.performance
    @pytest.mark.slow
    def test_async_handler_concurrent_submissions(self, lambda_context):
        """Test async handler performance under concurrent load."""

        def make_request():
            event = {
                "httpMethod": "POST",
                "path": "/analyze/async",
                "body": json.dumps(
                    {
                        "text": f"Test text {time.time()}",
                        "source_id": f"test-source-{time.time()}",
                    }
                ),
                "headers": {
                    "Content-Type": "application/json",
                    "X-API-Key": "test-api-key",
                },
                "requestContext": {"requestId": f"test-request-{time.time()}"},
            }

            with patch("src.handlers.async_handler._store_job") as mock_store_job:
                mock_store_job.return_value = True

                with patch(
                    "src.handlers.async_handler._store_document"
                ) as mock_store_doc:
                    mock_store_doc.return_value = True

                    with patch(
                        "src.handlers.async_handler._start_step_function"
                    ) as mock_start_sf:
                        mock_start_sf.return_value = True

                        start_time = time.time()
                        response = async_handler(event, lambda_context)
                        end_time = time.time()

                        return {
                            "status_code": response["statusCode"],
                            "response_time": (end_time - start_time) * 1000,
                        }

        # Run 5 concurrent requests (async handler is more resource intensive)
        num_requests = 5
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in futures]

        # Analyze results
        successful_requests = [r for r in results if r["status_code"] == 202]
        response_times = [r["response_time"] for r in successful_requests]

        assert len(successful_requests) == num_requests
        assert (
            max(response_times) < 3000
        )  # All requests should complete within 3 seconds
        assert (
            sum(response_times) / len(response_times) < 2000
        )  # Average should be under 2 seconds

    @pytest.mark.performance
    def test_memory_usage_large_text(self, lambda_context):
        """Test memory usage with large text processing."""
        import os

        import psutil

        # Get current process
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create large text
        large_text = "This is a test sentence. " * 50000  # ~1.25MB

        event = {
            "httpMethod": "POST",
            "path": "/analyze/sync",
            "body": json.dumps({"text": large_text}),
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": "test-api-key",
            },
            "requestContext": {"requestId": "test-request-id"},
        }

        with patch("src.handlers.sync_handler._analyze_sentiment") as mock_analyze:
            mock_analyze.return_value = {
                "Sentiment": "POSITIVE",
                "SentimentScore": {
                    "Positive": 0.95,
                    "Negative": 0.02,
                    "Neutral": 0.02,
                    "Mixed": 0.01,
                },
                "LanguageCode": "en",
            }

            with patch("src.handlers.sync_handler.SentimentCache") as mock_cache:
                mock_cache.return_value.get_cached_result.return_value = None
                mock_cache.return_value.store_result.return_value = True

                with patch("src.handlers.sync_handler.PIIDetector") as mock_pii:
                    mock_pii.return_value.detect_pii.return_value = {
                        "pii_detected": False
                    }

                    response = sync_handler(event, lambda_context)

                    final_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_increase = final_memory - initial_memory

                    assert response["statusCode"] == 200
                    assert (
                        memory_increase < 100
                    )  # Should not increase memory by more than 100MB
