"""Integration tests for API endpoints."""

import pytest
import json
import time
from moto import mock_aws
import boto3
from unittest.mock import patch

from src.handlers.sync_handler import lambda_handler as sync_handler
from src.handlers.async_handler import lambda_handler as async_handler
from src.handlers.status_handler import lambda_handler as status_handler
from src.handlers.health_handler import lambda_handler as health_handler


class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.fixture
    def mock_aws_services(self):
        """Mock AWS services for integration testing."""
        with mock_aws(['dynamodb', 's3', 'stepfunctions']):
            # Set up DynamoDB tables
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            
            # Create sentiment cache table
            cache_table = dynamodb.create_table(
                TableName='test-sentiment-cache',
                KeySchema=[{'AttributeName': 'text_hash', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'text_hash', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Create job results table
            job_table = dynamodb.create_table(
                TableName='test-job-results',
                KeySchema=[{'AttributeName': 'job_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'job_id', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Create S3 bucket
            s3 = boto3.client('s3', region_name='us-east-1')
            s3.create_bucket(Bucket='test-aurastream-documents')
            
            # Create Step Functions state machine
            stepfunctions = boto3.client('stepfunctions', region_name='us-east-1')
            stepfunctions.create_state_machine(
                name='test-sentiment-analysis',
                definition=json.dumps({
                    "Comment": "Test state machine",
                    "StartAt": "ProcessDocument",
                    "States": {
                        "ProcessDocument": {
                            "Type": "Pass",
                            "Result": "Success",
                            "End": True
                        }
                    }
                }),
                roleArn='arn:aws:iam::123456789012:role/TestRole'
            )
            
            yield {
                'cache_table': cache_table,
                'job_table': job_table,
                's3': s3,
                'stepfunctions': stepfunctions
            }
    
    @pytest.fixture
    def sync_event(self):
        """Sample sync API event."""
        return {
            'httpMethod': 'POST',
            'path': '/analyze/sync',
            'body': json.dumps({
                'text': 'I love this product!',
                'options': {
                    'language_code': 'en',
                    'include_confidence': True,
                    'include_pii_detection': True
                }
            }),
            'headers': {
                'Content-Type': 'application/json',
                'X-API-Key': 'test-api-key'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
    
    @pytest.fixture
    def async_event(self):
        """Sample async API event."""
        return {
            'httpMethod': 'POST',
            'path': '/analyze/async',
            'body': json.dumps({
                'text': 'This is a longer text for async processing. ' * 100,
                'source_id': 'test-source-123',
                'options': {
                    'language_code': 'en',
                    'include_confidence': True
                }
            }),
            'headers': {
                'Content-Type': 'application/json',
                'X-API-Key': 'test-api-key'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
    
    @pytest.fixture
    def status_event(self):
        """Sample status API event."""
        return {
            'httpMethod': 'GET',
            'path': '/status/test-job-id',
            'pathParameters': {
                'job_id': 'test-job-id'
            },
            'headers': {
                'Content-Type': 'application/json',
                'X-API-Key': 'test-api-key'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
    
    @pytest.fixture
    def health_event(self):
        """Sample health API event."""
        return {
            'httpMethod': 'GET',
            'path': '/health',
            'headers': {
                'Content-Type': 'application/json'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
    
    @pytest.fixture
    def lambda_context(self):
        """Sample Lambda context."""
        context = type('Context', (), {})()
        context.aws_request_id = 'test-request-id'
        context.function_name = 'test-function'
        context.function_version = '1'
        context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test'
        context.memory_limit_in_mb = 512
        context.remaining_time_in_millis = lambda: 30000
        return context
    
    @patch('src.handlers.sync_handler._analyze_sentiment')
    def test_sync_endpoint_integration(self, mock_analyze, mock_aws_services, sync_event, lambda_context):
        """Test sync endpoint integration."""
        # Mock Comprehend response
        mock_analyze.return_value = {
            'Sentiment': 'POSITIVE',
            'SentimentScore': {
                'Positive': 0.95,
                'Negative': 0.02,
                'Neutral': 0.02,
                'Mixed': 0.01
            },
            'LanguageCode': 'en'
        }
        
        # Call sync handler
        response = sync_handler(sync_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['sentiment'] == 'POSITIVE'
        assert body['score'] == 0.95
        assert body['language_code'] == 'en'
        assert 'request_id' in body
    
    def test_async_endpoint_integration(self, mock_aws_services, async_event, lambda_context):
        """Test async endpoint integration."""
        # Call async handler
        response = async_handler(async_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 202
        body = json.loads(response['body'])
        assert body['status'] == 'PROCESSING'
        assert 'job_id' in body
        assert 'estimated_completion' in body
        
        # Verify job was stored in DynamoDB
        job_table = mock_aws_services['job_table']
        job_id = body['job_id']
        
        job_response = job_table.get_item(Key={'job_id': job_id})
        assert 'Item' in job_response
        assert job_response['Item']['status'] == 'PROCESSING'
        assert job_response['Item']['source_id'] == 'test-source-123'
        
        # Verify document was stored in S3
        s3 = mock_aws_services['s3']
        try:
            s3.get_object(Bucket='test-aurastream-documents', Key=f'documents/{job_id}.txt')
        except s3.exceptions.NoSuchKey:
            pytest.fail("Document was not stored in S3")
    
    def test_status_endpoint_integration(self, mock_aws_services, status_event, lambda_context):
        """Test status endpoint integration."""
        # Create a test job in DynamoDB
        job_table = mock_aws_services['job_table']
        job_table.put_item(Item={
            'job_id': 'test-job-id',
            'status': 'COMPLETED',
            'created_at': '2024-01-01T00:00:00Z',
            'completed_at': '2024-01-01T00:01:00Z',
            'result': {
                'sentiment': 'POSITIVE',
                'score': 0.95
            },
            'source_id': 'test-source-123'
        })
        
        # Call status handler
        response = status_handler(status_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['job_id'] == 'test-job-id'
        assert body['status'] == 'COMPLETED'
        assert body['result']['sentiment'] == 'POSITIVE'
        assert body['source_id'] == 'test-source-123'
    
    def test_status_endpoint_not_found(self, mock_aws_services, status_event, lambda_context):
        """Test status endpoint with non-existent job."""
        # Call status handler without creating job
        response = status_handler(status_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error']['code'] == 'NOT_FOUND'
        assert 'Job not found' in body['error']['message']
    
    def test_health_endpoint_integration(self, mock_aws_services, health_event, lambda_context):
        """Test health endpoint integration."""
        # Call health handler
        response = health_handler(health_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'healthy'
        assert body['version'] == '1.0.0'
        assert 'components' in body
        assert 'timestamp' in body
    
    def test_sync_endpoint_validation_error(self, mock_aws_services, lambda_context):
        """Test sync endpoint with validation error."""
        # Create invalid event
        invalid_event = {
            'httpMethod': 'POST',
            'path': '/analyze/sync',
            'body': json.dumps({
                'text': ''  # Empty text should fail validation
            }),
            'headers': {
                'Content-Type': 'application/json'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
        
        # Call sync handler
        response = sync_handler(invalid_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'VALIDATION_ERROR'
    
    def test_async_endpoint_validation_error(self, mock_aws_services, lambda_context):
        """Test async endpoint with validation error."""
        # Create invalid event with text too long
        long_text = 'x' * 1048577  # Exceeds 1MB limit
        invalid_event = {
            'httpMethod': 'POST',
            'path': '/analyze/async',
            'body': json.dumps({
                'text': long_text
            }),
            'headers': {
                'Content-Type': 'application/json'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
        
        # Call async handler
        response = async_handler(invalid_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'VALIDATION_ERROR'
        assert 'exceeds maximum length' in body['error']['message']
    
    def test_status_endpoint_validation_error(self, mock_aws_services, lambda_context):
        """Test status endpoint with invalid job ID."""
        # Create invalid event
        invalid_event = {
            'httpMethod': 'GET',
            'path': '/status/invalid-job-id',
            'pathParameters': {
                'job_id': 'invalid-job-id'  # Not a valid UUID
            },
            'headers': {
                'Content-Type': 'application/json'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
        
        # Call status handler
        response = status_handler(invalid_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'VALIDATION_ERROR'
        assert 'Invalid job ID format' in body['error']['message']
