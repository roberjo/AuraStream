"""Metrics collection and monitoring for AuraStream."""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

import boto3
from src.utils.constants import METRICS_NAMESPACE

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and sends custom metrics to CloudWatch."""
    
    def __init__(self):
        """Initialize metrics collector."""
        region = os.environ.get('AWS_REGION', 'us-east-1')
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.namespace = METRICS_NAMESPACE
        self.environment = os.environ.get('ENVIRONMENT', 'dev')
    
    def record_sentiment_analysis(self, sentiment: str, confidence: float, processing_time: int):
        """
        Record sentiment analysis metrics.
        
        Args:
            sentiment: Sentiment result
            confidence: Confidence score
            processing_time: Processing time in milliseconds
        """
        try:
            metrics = [
                {
                    'MetricName': 'SentimentAnalysisCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Sentiment', 'Value': sentiment},
                        {'Name': 'Environment', 'Value': self.environment}
                    ]
                },
                {
                    'MetricName': 'SentimentConfidence',
                    'Value': confidence,
                    'Unit': 'None',
                    'Dimensions': [
                        {'Name': 'Sentiment', 'Value': sentiment},
                        {'Name': 'Environment', 'Value': self.environment}
                    ]
                },
                {
                    'MetricName': 'ProcessingTime',
                    'Value': processing_time,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'Sentiment', 'Value': sentiment},
                        {'Name': 'Environment', 'Value': self.environment}
                    ]
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metrics
            )
            
            logger.debug(f"Recorded sentiment analysis metrics for {sentiment}")
            
        except Exception as e:
            logger.error(f"Error recording sentiment analysis metrics: {str(e)}")
    
    def record_cache_hit(self):
        """Record cache hit metric."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': 'CacheHitCount',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'Environment', 'Value': self.environment}
                        ]
                    }
                ]
            )
            
            logger.debug("Recorded cache hit metric")
            
        except Exception as e:
            logger.error(f"Error recording cache hit metric: {str(e)}")
    
    def record_cache_miss(self):
        """Record cache miss metric."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': 'CacheMissCount',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'Environment', 'Value': self.environment}
                        ]
                    }
                ]
            )
            
            logger.debug("Recorded cache miss metric")
            
        except Exception as e:
            logger.error(f"Error recording cache miss metric: {str(e)}")
    
    def record_pii_detection(self):
        """Record PII detection metric."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': 'PIIDetectionCount',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'Environment', 'Value': self.environment}
                        ]
                    }
                ]
            )
            
            logger.debug("Recorded PII detection metric")
            
        except Exception as e:
            logger.error(f"Error recording PII detection metric: {str(e)}")
    
    def record_error(self, error_type: str = 'general'):
        """
        Record error metric.
        
        Args:
            error_type: Type of error
        """
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': 'ErrorCount',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'ErrorType', 'Value': error_type},
                            {'Name': 'Environment', 'Value': self.environment}
                        ]
                    }
                ]
            )
            
            logger.debug(f"Recorded error metric for {error_type}")
            
        except Exception as e:
            logger.error(f"Error recording error metric: {str(e)}")
    
    def record_api_usage(self, endpoint: str, customer_id: str, response_time: int, status_code: int):
        """
        Record API usage metrics.
        
        Args:
            endpoint: API endpoint
            customer_id: Customer identifier
            response_time: Response time in milliseconds
            status_code: HTTP status code
        """
        try:
            metrics = [
                {
                    'MetricName': 'APIRequestCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': endpoint},
                        {'Name': 'CustomerId', 'Value': customer_id},
                        {'Name': 'StatusCode', 'Value': str(status_code)},
                        {'Name': 'Environment', 'Value': self.environment}
                    ]
                },
                {
                    'MetricName': 'APIResponseTime',
                    'Value': response_time,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': endpoint},
                        {'Name': 'CustomerId', 'Value': customer_id},
                        {'Name': 'Environment', 'Value': self.environment}
                    ]
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metrics
            )
            
            logger.debug(f"Recorded API usage metrics for {endpoint}")
            
        except Exception as e:
            logger.error(f"Error recording API usage metrics: {str(e)}")
    
    def record_business_metric(self, metric_name: str, value: float, unit: str = 'Count', 
                             dimensions: Optional[Dict[str, str]] = None):
        """
        Record custom business metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit
            dimensions: Additional dimensions
        """
        try:
            metric_dimensions = [
                {'Name': 'Environment', 'Value': self.environment}
            ]
            
            if dimensions:
                for key, value in dimensions.items():
                    metric_dimensions.append({'Name': key, 'Value': value})
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Dimensions': metric_dimensions
                    }
                ]
            )
            
            logger.debug(f"Recorded business metric: {metric_name}")
            
        except Exception as e:
            logger.error(f"Error recording business metric {metric_name}: {str(e)}")
