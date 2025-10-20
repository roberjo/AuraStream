"""Integration tests for AWS services."""

import boto3
import pytest
from moto import mock_aws

from src.cache.sentiment_cache import SentimentCache
from src.monitoring.metrics import MetricsCollector
from src.pii.pii_detector import PIIDetector


class TestAWSServicesIntegration:
    """Integration tests for AWS services."""

    @pytest.fixture
    @mock_aws
    def mock_aws_services(self):
        """Mock AWS services for integration testing."""
        # Set up DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-sentiment-cache",
            KeySchema=[{"AttributeName": "text_hash", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "text_hash", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Set up S3
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-aurastream-documents")

        # Set up Comprehend
        comprehend = boto3.client("comprehend", region_name="us-east-1")

        yield {
            "dynamodb": dynamodb,
            "table": table,
            "s3": s3,
            "comprehend": comprehend,
        }

    def test_sentiment_cache_integration(self, mock_aws_services):
        """Test sentiment cache integration with DynamoDB."""
        # Set environment variable
        import os

        os.environ["SENTIMENT_CACHE_TABLE"] = "test-sentiment-cache"

        # Create cache instance
        cache = SentimentCache()

        # Test storing result
        test_result = {"sentiment": "POSITIVE", "score": 0.95, "language_code": "en"}

        success = cache.store_result("I love this product!", test_result)
        assert success is True

        # Test retrieving result
        cached_result = cache.get_cached_result("I love this product!")
        assert cached_result is not None
        assert cached_result["sentiment"] == "POSITIVE"
        assert cached_result["score"] == 0.95

        # Test cache miss
        cached_result = cache.get_cached_result("I hate this product!")
        assert cached_result is None

        # Test cache stats
        stats = cache.get_cache_stats()
        assert stats["total_items"] == 1
        assert stats["table_name"] == "test-sentiment-cache"

    def test_pii_detector_integration(self, mock_aws_services):
        """Test PII detector integration with Comprehend."""
        # Mock Comprehend response
        mock_aws_services["comprehend"].detect_pii_entities = lambda **kwargs: {
            "Entities": [
                {"Type": "EMAIL", "BeginOffset": 12, "EndOffset": 30, "Score": 0.99}
            ],
            "Confidence": 0.99,
        }

        # Create PII detector instance
        detector = PIIDetector()

        # Test PII detection
        result = detector.detect_pii("Contact me at john.doe@example.com")

        assert result["pii_detected"] is True
        assert len(result["entities"]) == 1
        assert result["entities"][0]["Type"] == "EMAIL"
        assert result["confidence"] == 0.99

        # Test PII redaction
        redacted_text = detector.redact_pii(
            "Contact me at john.doe@example.com", result["entities"]
        )
        assert "[EMAIL]" in redacted_text
        assert "john.doe@example.com" not in redacted_text

    def test_metrics_collector_integration(self, mock_aws_services):
        """Test metrics collector integration with CloudWatch."""
        # Create metrics collector instance
        metrics = MetricsCollector()

        # Test recording metrics (will use mocked CloudWatch)
        metrics.record_sentiment_analysis("POSITIVE", 0.95, 500)
        metrics.record_cache_hit()
        metrics.record_pii_detection()
        metrics.record_error("test_error")

        # Test recording API usage
        metrics.record_api_usage(
            endpoint="/analyze/sync",
            customer_id="test-customer",
            response_time=300,
            status_code=200,
        )

        # Test recording business metrics
        metrics.record_business_metric(
            "TestMetric", 1.0, "Count", {"Environment": "test"}
        )

        # All operations should complete without errors
        assert True

    def test_s3_document_storage_integration(self, mock_aws_services):
        """Test S3 document storage integration."""
        s3 = mock_aws_services["s3"]
        bucket_name = "test-aurastream-documents"

        # Test storing document
        test_text = "This is a test document for sentiment analysis."
        job_id = "test-job-123"

        s3.put_object(
            Bucket=bucket_name,
            Key=f"documents/{job_id}.txt",
            Body=test_text.encode("utf-8"),
            ContentType="text/plain",
            Metadata={"job_id": job_id, "created_at": "2024-01-01T00:00:00Z"},
        )

        # Test retrieving document
        response = s3.get_object(Bucket=bucket_name, Key=f"documents/{job_id}.txt")

        retrieved_text = response["Body"].read().decode("utf-8")
        assert retrieved_text == test_text
        assert response["Metadata"]["job_id"] == job_id

    def test_dynamodb_job_storage_integration(self, mock_aws_services):
        """Test DynamoDB job storage integration."""
        dynamodb = mock_aws_services["dynamodb"]

        # Create job results table
        job_table = dynamodb.create_table(
            TableName="test-job-results",
            KeySchema=[{"AttributeName": "job_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "job_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Test storing job
        job_id = "test-job-456"
        job_item = {
            "job_id": job_id,
            "status": "PROCESSING",
            "created_at": "2024-01-01T00:00:00Z",
            "source_id": "test-source-123",
            "text_length": 100,
            "options": {"language_code": "en"},
        }

        job_table.put_item(Item=job_item)

        # Test retrieving job
        response = job_table.get_item(Key={"job_id": job_id})
        assert "Item" in response
        assert response["Item"]["status"] == "PROCESSING"
        assert response["Item"]["source_id"] == "test-source-123"

        # Test updating job
        job_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #status = :status, #completed_at = :completed_at",
            ExpressionAttributeNames={
                "#status": "status",
                "#completed_at": "completed_at",
            },
            ExpressionAttributeValues={
                ":status": "COMPLETED",
                ":completed_at": "2024-01-01T00:01:00Z",
            },
        )

        # Verify update
        response = job_table.get_item(Key={"job_id": job_id})
        assert response["Item"]["status"] == "COMPLETED"
        assert response["Item"]["completed_at"] == "2024-01-01T00:01:00Z"

    def test_comprehend_sentiment_analysis_integration(self, mock_aws_services):
        """Test Comprehend sentiment analysis integration."""
        comprehend = mock_aws_services["comprehend"]

        # Mock sentiment detection response
        comprehend.detect_sentiment = lambda **kwargs: {
            "Sentiment": "POSITIVE",
            "SentimentScore": {
                "Positive": 0.95,
                "Negative": 0.02,
                "Neutral": 0.02,
                "Mixed": 0.01,
            },
            "LanguageCode": "en",
        }

        # Test sentiment analysis
        response = comprehend.detect_sentiment(
            Text="I love this product!", LanguageCode="en"
        )

        assert response["Sentiment"] == "POSITIVE"
        assert response["SentimentScore"]["Positive"] == 0.95
        assert response["LanguageCode"] == "en"

    def test_comprehend_pii_detection_integration(self, mock_aws_services):
        """Test Comprehend PII detection integration."""
        comprehend = mock_aws_services["comprehend"]

        # Mock PII detection response
        comprehend.detect_pii_entities = lambda **kwargs: {
            "Entities": [
                {"Type": "EMAIL", "BeginOffset": 12, "EndOffset": 30, "Score": 0.99},
                {"Type": "PHONE", "BeginOffset": 35, "EndOffset": 47, "Score": 0.98},
            ],
            "Confidence": 0.99,
        }

        # Test PII detection
        response = comprehend.detect_pii_entities(
            Text="Contact me at john.doe@example.com or call (555) 123-4567",
            LanguageCode="en",
        )

        assert len(response["Entities"]) == 2
        assert response["Entities"][0]["Type"] == "EMAIL"
        assert response["Entities"][1]["Type"] == "PHONE"
        assert response["Confidence"] == 0.99

    def test_error_handling_integration(self, mock_aws_services):
        """Test error handling in AWS service integrations."""
        # Test cache error handling
        import os

        os.environ["SENTIMENT_CACHE_TABLE"] = "non-existent-table"

        cache = SentimentCache()

        # Should handle error gracefully
        result = cache.get_cached_result("test text")
        assert result is None

        # Test PII detector error handling
        detector = PIIDetector()

        # Mock Comprehend error
        mock_aws_services["comprehend"].detect_pii_entities = lambda **kwargs: {
            "Entities": [],
            "Confidence": 0.0,
            "error": "Service unavailable",
        }

        result = detector.detect_pii("test text")
        assert result["pii_detected"] is False
        assert "error" in result
