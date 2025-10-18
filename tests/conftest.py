"""Pytest configuration and fixtures."""

import pytest
import os
from unittest.mock import Mock, patch
from moto import mock_dynamodb, mock_s3
import boto3


@pytest.fixture
def mock_aws_services():
    """Mock AWS services for testing."""
    with mock_dynamodb(), mock_s3():
        yield


@pytest.fixture
def dynamodb_table():
    """Create DynamoDB table for testing."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-sentiment-cache',
        KeySchema=[{'AttributeName': 'text_hash', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'text_hash', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    yield table


@pytest.fixture
def s3_bucket():
    """Create S3 bucket for testing."""
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'test-aurastream-documents'
    s3.create_bucket(Bucket=bucket_name)
    yield bucket_name


@pytest.fixture
def sample_texts():
    """Sample texts for testing."""
    return {
        'positive': "I absolutely love this product! It's amazing!",
        'negative': "This product is terrible! I hate it!",
        'neutral': "The weather is okay today.",
        'mixed': "I love the design but hate the price.",
        'pii_email': "Contact me at john.doe@example.com",
        'pii_phone': "Call me at (555) 123-4567",
        'pii_ssn': "My SSN is 123-45-6789"
    }


@pytest.fixture
def mock_comprehend_response():
    """Mock Comprehend API response."""
    return {
        'Sentiment': 'POSITIVE',
        'SentimentScore': {
            'Positive': 0.95,
            'Negative': 0.02,
            'Neutral': 0.02,
            'Mixed': 0.01
        },
        'LanguageCode': 'en'
    }


@pytest.fixture
def mock_pii_response():
    """Mock PII detection response."""
    return {
        'Entities': [
            {
                'Type': 'EMAIL',
                'BeginOffset': 12,
                'EndOffset': 30,
                'Score': 0.99
            }
        ],
        'Confidence': 0.99
    }


@pytest.fixture
def api_event():
    """Sample API Gateway event."""
    return {
        'httpMethod': 'POST',
        'path': '/analyze/sync',
        'body': '{"text": "I love this product!"}',
        'headers': {
            'Content-Type': 'application/json',
            'X-API-Key': 'test-api-key'
        },
        'requestContext': {
            'requestId': 'test-request-id'
        }
    }


@pytest.fixture
def lambda_context():
    """Sample Lambda context."""
    context = Mock()
    context.aws_request_id = 'test-request-id'
    context.function_name = 'test-function'
    context.function_version = '1'
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test'
    context.memory_limit_in_mb = 512
    context.remaining_time_in_millis = lambda: 30000
    return context


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ.update({
        'SENTIMENT_CACHE_TABLE': 'test-sentiment-cache',
        'JOB_RESULTS_TABLE': 'test-job-results',
        'DOCUMENTS_BUCKET': 'test-documents-bucket',
        'ENVIRONMENT': 'test',
        'LOG_LEVEL': 'DEBUG'
    })
    yield
    # Clean up environment variables
    for key in ['SENTIMENT_CACHE_TABLE', 'JOB_RESULTS_TABLE', 'DOCUMENTS_BUCKET', 'ENVIRONMENT', 'LOG_LEVEL']:
        os.environ.pop(key, None)
