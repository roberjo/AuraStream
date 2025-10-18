"""End-to-end tests for complete AuraStream workflows."""

import pytest
import json
import time
from moto import mock_dynamodb, mock_s3, mock_stepfunctions, mock_comprehend
import boto3
from unittest.mock import patch

from src.handlers.sync_handler import lambda_handler as sync_handler
from src.handlers.async_handler import lambda_handler as async_handler
from src.handlers.status_handler import lambda_handler as status_handler
from src.handlers.health_handler import lambda_handler as health_handler


class TestCompleteWorkflow:
    """End-to-end tests for complete workflows."""
    
    @pytest.fixture
    def mock_aws_services(self):
        """Mock AWS services for E2E testing."""
        with mock_dynamodb(), mock_s3(), mock_stepfunctions(), mock_comprehend():
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
            state_machine = stepfunctions.create_state_machine(
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
            
            # Set up Comprehend
            comprehend = boto3.client('comprehend', region_name='us-east-1')
            
            yield {
                'cache_table': cache_table,
                'job_table': job_table,
                's3': s3,
                'stepfunctions': stepfunctions,
                'state_machine_arn': state_machine['stateMachineArn'],
                'comprehend': comprehend
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
    def test_complete_sync_workflow(self, mock_analyze, mock_aws_services, lambda_context):
        """Test complete synchronous sentiment analysis workflow."""
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
        
        # Test sync analysis
        sync_event = {
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
        
        response = sync_handler(sync_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['sentiment'] == 'POSITIVE'
        assert body['score'] == 0.95
        assert body['language_code'] == 'en'
        assert body['cache_hit'] is False
        
        # Test caching by making the same request again
        response2 = sync_handler(sync_event, lambda_context)
        body2 = json.loads(response2['body'])
        assert body2['cache_hit'] is True
        assert body2['sentiment'] == 'POSITIVE'
    
    def test_complete_async_workflow(self, mock_aws_services, lambda_context):
        """Test complete asynchronous sentiment analysis workflow."""
        # Set environment variables
        import os
        os.environ['JOB_RESULTS_TABLE'] = 'test-job-results'
        os.environ['DOCUMENTS_BUCKET'] = 'test-aurastream-documents'
        os.environ['STEP_FUNCTION_ARN'] = mock_aws_services['state_machine_arn']
        
        # Test async analysis
        async_event = {
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
        
        response = async_handler(async_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 202
        body = json.loads(response['body'])
        assert body['status'] == 'PROCESSING'
        assert 'job_id' in body
        assert 'estimated_completion' in body
        
        job_id = body['job_id']
        
        # Verify job was stored in DynamoDB
        job_table = mock_aws_services['job_table']
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
        
        # Test status check
        status_event = {
            'httpMethod': 'GET',
            'path': f'/status/{job_id}',
            'pathParameters': {
                'job_id': job_id
            },
            'headers': {
                'Content-Type': 'application/json',
                'X-API-Key': 'test-api-key'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
        
        status_response = status_handler(status_event, lambda_context)
        assert status_response['statusCode'] == 200
        status_body = json.loads(status_response['body'])
        assert status_body['job_id'] == job_id
        assert status_body['status'] == 'PROCESSING'
    
    def test_health_check_workflow(self, mock_aws_services, lambda_context):
        """Test health check workflow."""
        # Mock Comprehend health check
        mock_aws_services['comprehend'].detect_sentiment = lambda **kwargs: {
            'Sentiment': 'POSITIVE',
            'SentimentScore': {'Positive': 0.95, 'Negative': 0.02, 'Neutral': 0.02, 'Mixed': 0.01},
            'LanguageCode': 'en'
        }
        
        health_event = {
            'httpMethod': 'GET',
            'path': '/health',
            'headers': {
                'Content-Type': 'application/json'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
        
        response = health_handler(health_event, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'healthy'
        assert body['version'] == '1.0.0'
        assert 'components' in body
        assert 'timestamp' in body
    
    def test_error_handling_workflow(self, mock_aws_services, lambda_context):
        """Test error handling workflow."""
        # Test sync endpoint with invalid input
        invalid_sync_event = {
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
        
        response = sync_handler(invalid_sync_event, lambda_context)
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'VALIDATION_ERROR'
        
        # Test async endpoint with text too long
        long_text = 'x' * 1048577  # Exceeds 1MB limit
        invalid_async_event = {
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
        
        response = async_handler(invalid_async_event, lambda_context)
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'VALIDATION_ERROR'
        
        # Test status endpoint with non-existent job
        status_event = {
            'httpMethod': 'GET',
            'path': '/status/non-existent-job',
            'pathParameters': {
                'job_id': 'non-existent-job'
            },
            'headers': {
                'Content-Type': 'application/json'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
        
        response = status_handler(status_event, lambda_context)
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error']['code'] == 'NOT_FOUND'
    
    def test_security_validation_workflow(self, mock_aws_services, lambda_context):
        """Test security validation workflow."""
        # Test with potentially malicious input
        malicious_event = {
            'httpMethod': 'POST',
            'path': '/analyze/sync',
            'body': json.dumps({
                'text': "'; DROP TABLE users; --"  # SQL injection attempt
            }),
            'headers': {
                'Content-Type': 'application/json'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
        
        response = sync_handler(malicious_event, lambda_context)
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'VALIDATION_ERROR'
        assert 'malicious content' in body['error']['message']
        
        # Test with XSS attempt
        xss_event = {
            'httpMethod': 'POST',
            'path': '/analyze/sync',
            'body': json.dumps({
                'text': '<script>alert("xss")</script>'  # XSS attempt
            }),
            'headers': {
                'Content-Type': 'application/json'
            },
            'requestContext': {
                'requestId': 'test-request-id'
            }
        }
        
        response = sync_handler(xss_event, lambda_context)
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'VALIDATION_ERROR'
        assert 'malicious content' in body['error']['message']
    
    def test_performance_workflow(self, mock_aws_services, lambda_context):
        """Test performance characteristics of the workflow."""
        # Mock Comprehend response
        with patch('src.handlers.sync_handler._analyze_sentiment') as mock_analyze:
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
            
            # Test multiple requests to verify caching performance
            sync_event = {
                'httpMethod': 'POST',
                'path': '/analyze/sync',
                'body': json.dumps({
                    'text': 'I love this product!',
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
            
            # First request (cache miss)
            start_time = time.time()
            response1 = sync_handler(sync_event, lambda_context)
            first_request_time = time.time() - start_time
            
            # Second request (cache hit)
            start_time = time.time()
            response2 = sync_handler(sync_event, lambda_context)
            second_request_time = time.time() - start_time
            
            # Verify responses
            assert response1['statusCode'] == 200
            assert response2['statusCode'] == 200
            
            body1 = json.loads(response1['body'])
            body2 = json.loads(response2['body'])
            
            assert body1['cache_hit'] is False
            assert body2['cache_hit'] is True
            
            # Cache hit should be faster
            assert second_request_time < first_request_time
            
            # Both should return the same result
            assert body1['sentiment'] == body2['sentiment']
            assert body1['score'] == body2['score']
