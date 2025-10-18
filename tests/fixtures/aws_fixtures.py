"""AWS service fixtures for testing."""

import pytest
from moto import mock_aws
from unittest.mock import Mock, patch
import boto3
import json
from datetime import datetime, timezone


@pytest.fixture
def mock_aws_services():
    """Mock AWS services for testing."""
    with mock_aws(['dynamodb', 's3', 'stepfunctions', 'comprehend', 'cloudwatch']):
        yield


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB service."""
    with mock_aws(['dynamodb']):
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        yield dynamodb


@pytest.fixture
def mock_s3():
    """Mock S3 service."""
    with mock_aws(['s3']):
        s3 = boto3.client('s3', region_name='us-east-1')
        yield s3


@pytest.fixture
def mock_stepfunctions():
    """Mock Step Functions service."""
    with mock_aws(['stepfunctions']):
        stepfunctions = boto3.client('stepfunctions', region_name='us-east-1')
        yield stepfunctions


@pytest.fixture
def mock_comprehend():
    """Mock Comprehend service."""
    with mock_aws(['comprehend']):
        comprehend = boto3.client('comprehend', region_name='us-east-1')
        yield comprehend


@pytest.fixture
def mock_cloudwatch():
    """Mock CloudWatch service."""
    with mock_aws(['cloudwatch']):
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        yield cloudwatch


@pytest.fixture
def sample_comprehend_response():
    """Sample Comprehend sentiment analysis response."""
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
def sample_job_data():
    """Sample job data for testing."""
    return {
        'job_id': 'test-job-123',
        'status': 'PROCESSING',
        'text': 'I love this product!',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'source_id': 'test-source',
        'options': {
            'include_confidence': True,
            'include_pii_detection': True
        }
    }


@pytest.fixture
def sample_document_data():
    """Sample document data for S3 storage."""
    return {
        'bucket': 'aurastream-documents',
        'key': 'documents/test-job-123.json',
        'content': json.dumps({
            'text': 'I love this product!',
            'source_id': 'test-source',
            'options': {
                'include_confidence': True,
                'include_pii_detection': True
            }
        })
    }


@pytest.fixture
def mock_lambda_context():
    """Mock Lambda context for testing."""
    context = Mock()
    context.aws_request_id = 'test-request-id'
    context.function_name = 'test-function'
    context.function_version = '1'
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
    context.memory_limit_in_mb = 128
    context.remaining_time_in_millis = lambda: 30000
    return context


@pytest.fixture
def mock_api_gateway_event():
    """Mock API Gateway event."""
    return {
        'httpMethod': 'POST',
        'path': '/analyze/sync',
        'body': '{"text": "I love this product!"}',
        'headers': {
            'Content-Type': 'application/json',
            'X-API-Key': 'test-api-key'
        },
        'requestContext': {
            'requestId': 'test-request-id',
            'identity': {
                'sourceIp': '127.0.0.1'
            }
        },
        'pathParameters': None,
        'queryStringParameters': None,
        'stageVariables': None
    }


@pytest.fixture
def mock_async_api_gateway_event():
    """Mock API Gateway event for async endpoint."""
    return {
        'httpMethod': 'POST',
        'path': '/analyze/async',
        'body': '{"text": "I love this product!", "source_id": "test-source"}',
        'headers': {
            'Content-Type': 'application/json',
            'X-API-Key': 'test-api-key'
        },
        'requestContext': {
            'requestId': 'test-request-id',
            'identity': {
                'sourceIp': '127.0.0.1'
            }
        },
        'pathParameters': None,
        'queryStringParameters': None,
        'stageVariables': None
    }


@pytest.fixture
def mock_status_api_gateway_event():
    """Mock API Gateway event for status endpoint."""
    return {
        'httpMethod': 'GET',
        'path': '/status/test-job-123',
        'body': None,
        'headers': {
            'Content-Type': 'application/json',
            'X-API-Key': 'test-api-key'
        },
        'requestContext': {
            'requestId': 'test-request-id',
            'identity': {
                'sourceIp': '127.0.0.1'
            }
        },
        'pathParameters': {
            'job_id': 'test-job-123'
        },
        'queryStringParameters': None,
        'stageVariables': None
    }


@pytest.fixture
def mock_health_api_gateway_event():
    """Mock API Gateway event for health endpoint."""
    return {
        'httpMethod': 'GET',
        'path': '/health',
        'body': None,
        'headers': {
            'Content-Type': 'application/json'
        },
        'requestContext': {
            'requestId': 'test-request-id',
            'identity': {
                'sourceIp': '127.0.0.1'
            }
        },
        'pathParameters': None,
        'queryStringParameters': None,
        'stageVariables': None
    }
