"""Tests for metrics collection."""

import os
from unittest.mock import Mock, patch

from src.monitoring.metrics import MetricsCollector


class TestMetricsCollector:
    """Test metrics collection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "test"}):
            self.metrics = MetricsCollector()

    def test_init(self):
        """Test metrics collector initialization."""
        assert self.metrics.namespace == "AuraStream"
        assert self.metrics.environment == "test"

    @patch("src.monitoring.metrics.boto3.client")
    def test_record_sentiment_analysis_success(self, mock_boto_client):
        """Test successful sentiment analysis metrics recording."""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "test"}):
            metrics = MetricsCollector()
            metrics.record_sentiment_analysis("POSITIVE", 0.95, 150)

            mock_cloudwatch.put_metric_data.assert_called_once()
            call_args = mock_cloudwatch.put_metric_data.call_args
            assert call_args[1]["Namespace"] == "AuraStream"
            assert len(call_args[1]["MetricData"]) == 3

    @patch("src.monitoring.metrics.boto3.client")
    def test_record_sentiment_analysis_error(self, mock_boto_client):
        """Test sentiment analysis metrics recording with error."""
        mock_cloudwatch = Mock()
        mock_cloudwatch.put_metric_data.side_effect = Exception("CloudWatch error")
        mock_boto_client.return_value = mock_cloudwatch

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "test"}):
            metrics = MetricsCollector()
            # Should not raise exception
            metrics.record_sentiment_analysis("POSITIVE", 0.95, 150)

    @patch("src.monitoring.metrics.boto3.client")
    def test_record_cache_hit_success(self, mock_boto_client):
        """Test successful cache hit metrics recording."""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "test"}):
            metrics = MetricsCollector()
            metrics.record_cache_hit()

            mock_cloudwatch.put_metric_data.assert_called_once()
            call_args = mock_cloudwatch.put_metric_data.call_args
            assert call_args[1]["Namespace"] == "AuraStream"
            assert len(call_args[1]["MetricData"]) == 1
            assert call_args[1]["MetricData"][0]["MetricName"] == "CacheHitCount"

    @patch("src.monitoring.metrics.boto3.client")
    def test_record_cache_miss_success(self, mock_boto_client):
        """Test successful cache miss metrics recording."""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "test"}):
            metrics = MetricsCollector()
            metrics.record_cache_miss()

            mock_cloudwatch.put_metric_data.assert_called_once()
            call_args = mock_cloudwatch.put_metric_data.call_args
            assert call_args[1]["Namespace"] == "AuraStream"
            assert len(call_args[1]["MetricData"]) == 1
            assert call_args[1]["MetricData"][0]["MetricName"] == "CacheMissCount"

    @patch("src.monitoring.metrics.boto3.client")
    def test_record_pii_detection_success(self, mock_boto_client):
        """Test successful PII detection metrics recording."""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "test"}):
            metrics = MetricsCollector()
            metrics.record_pii_detection()

            mock_cloudwatch.put_metric_data.assert_called_once()
            call_args = mock_cloudwatch.put_metric_data.call_args
            assert call_args[1]["Namespace"] == "AuraStream"
            assert len(call_args[1]["MetricData"]) == 1
            assert call_args[1]["MetricData"][0]["MetricName"] == "PIIDetectionCount"

    @patch("src.monitoring.metrics.boto3.client")
    def test_record_error_success(self, mock_boto_client):
        """Test successful error metrics recording."""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "test"}):
            metrics = MetricsCollector()
            metrics.record_error("validation_error")

            mock_cloudwatch.put_metric_data.assert_called_once()
            call_args = mock_cloudwatch.put_metric_data.call_args
            assert call_args[1]["Namespace"] == "AuraStream"
            assert len(call_args[1]["MetricData"]) == 1
            assert call_args[1]["MetricData"][0]["MetricName"] == "ErrorCount"

    @patch("src.monitoring.metrics.boto3.client")
    def test_record_api_usage_success(self, mock_boto_client):
        """Test successful API usage metrics recording."""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "test"}):
            metrics = MetricsCollector()
            metrics.record_api_usage("/analyze", "customer123", 200, 200)

            mock_cloudwatch.put_metric_data.assert_called_once()
            call_args = mock_cloudwatch.put_metric_data.call_args
            assert call_args[1]["Namespace"] == "AuraStream"
            assert len(call_args[1]["MetricData"]) == 2
            assert call_args[1]["MetricData"][0]["MetricName"] == "APIRequestCount"
            assert call_args[1]["MetricData"][1]["MetricName"] == "APIResponseTime"

    @patch("src.monitoring.metrics.boto3.client")
    def test_record_business_metric_success(self, mock_boto_client):
        """Test successful business metric recording."""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "test"}):
            metrics = MetricsCollector()
            metrics.record_business_metric(
                "CustomMetric", 42.5, "Count", {"Type": "test"}
            )

            mock_cloudwatch.put_metric_data.assert_called_once()
            call_args = mock_cloudwatch.put_metric_data.call_args
            assert call_args[1]["Namespace"] == "AuraStream"
            assert len(call_args[1]["MetricData"]) == 1
            assert call_args[1]["MetricData"][0]["MetricName"] == "CustomMetric"
            assert call_args[1]["MetricData"][0]["Value"] == 42.5

    @patch("src.monitoring.metrics.boto3.client")
    def test_record_business_metric_without_dimensions(self, mock_boto_client):
        """Test business metric recording without additional dimensions."""
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "test"}):
            metrics = MetricsCollector()
            metrics.record_business_metric("SimpleMetric", 10.0)

            mock_cloudwatch.put_metric_data.assert_called_once()
            call_args = mock_cloudwatch.put_metric_data.call_args
            assert call_args[1]["Namespace"] == "AuraStream"
            assert len(call_args[1]["MetricData"]) == 1
            assert call_args[1]["MetricData"][0]["MetricName"] == "SimpleMetric"
            assert call_args[1]["MetricData"][0]["Value"] == 10.0

    @patch("src.monitoring.metrics.boto3.client")
    def test_record_business_metric_error(self, mock_boto_client):
        """Test business metric recording with error."""
        mock_cloudwatch = Mock()
        mock_cloudwatch.put_metric_data.side_effect = Exception("CloudWatch error")
        mock_boto_client.return_value = mock_cloudwatch

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "test"}):
            metrics = MetricsCollector()
            # Should not raise exception
            metrics.record_business_metric("ErrorMetric", 1.0)
