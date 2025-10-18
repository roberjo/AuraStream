"""Integration tests for Lambda handlers."""

import pytest
import json
from unittest.mock import patch, Mock
from tests.fixtures.aws_fixtures import (
    mock_aws_services,
    mock_lambda_context,
    mock_api_gateway_event,
    mock_async_api_gateway_event,
    mock_status_api_gateway_event,
    mock_health_api_gateway_event,
    sample_comprehend_response,
    sample_job_data
)


class TestSyncHandlerIntegration:
    """Integration tests for sync handler."""
    
    @pytest.mark.integration
    def test_sync_handler_full_workflow(self, mock_aws_services, mock_lambda_context, mock_api_gateway_event):
        """Test complete sync handler workflow."""
        from src.handlers.sync_handler import lambda_handler
        
        with patch('src.handlers.sync_handler._analyze_sentiment') as mock_analyze:
            mock_analyze.return_value = sample_comprehend_response
            
            with patch('src.handlers.sync_handler.SentimentCache') as mock_cache:
                mock_cache.return_value.get_cached_result.return_value = None
                mock_cache.return_value.store_result.return_value = True
                
                with patch('src.handlers.sync_handler.PIIDetector') as mock_pii:
                    mock_pii.return_value.detect_pii.return_value = {'pii_detected': False}
                    
                    response = lambda_handler(mock_api_gateway_event, mock_lambda_context)
                    
                    assert response['statusCode'] == 200
                    body = json.loads(response['body'])
                    assert body['sentiment'] == 'POSITIVE'
                    assert body['score'] == 0.95
                    assert body['language_code'] == 'en'
                    assert body['cache_hit'] is False
    
    @pytest.mark.integration
    def test_sync_handler_with_pii_detection(self, mock_aws_services, mock_lambda_context):
        """Test sync handler with PII detection enabled."""
        from src.handlers.sync_handler import lambda_handler
        
        # Create event with PII detection enabled
        event = mock_api_gateway_event.copy()
        event['body'] = json.dumps({
            "text": "Contact me at john.doe@example.com",
            "options": {"include_pii_detection": True}
        })
        
        with patch('src.handlers.sync_handler._analyze_sentiment') as mock_analyze:
            mock_analyze.return_value = sample_comprehend_response
            
            with patch('src.handlers.sync_handler.SentimentCache') as mock_cache:
                mock_cache.return_value.get_cached_result.return_value = None
                mock_cache.return_value.store_result.return_value = True
                
                with patch('src.handlers.sync_handler.PIIDetector') as mock_pii:
                    mock_pii.return_value.detect_pii.return_value = {
                        'pii_detected': True,
                        'pii_types': ['EMAIL'],
                        'pii_entities': [{
                            'type': 'EMAIL',
                            'value': 'john.doe@example.com',
                            'start': 0,
                            'end': 20,
                            'confidence': 0.99
                        }]
                    }
                    
                    response = lambda_handler(event, mock_lambda_context)
                    
                    assert response['statusCode'] == 200
                    body = json.loads(response['body'])
                    assert body['pii_detected'] is True
    
    @pytest.mark.integration
    def test_sync_handler_cache_hit(self, mock_aws_services, mock_lambda_context, mock_api_gateway_event):
        """Test sync handler with cache hit."""
        from src.handlers.sync_handler import lambda_handler
        
        cached_result = {
            'sentiment': 'POSITIVE',
            'score': 0.95,
            'language_code': 'en',
            'confidence': True,
            'pii_detected': False,
            'processing_time_ms': 50
        }
        
        with patch('src.handlers.sync_handler.SentimentCache') as mock_cache:
            mock_cache.return_value.get_cached_result.return_value = cached_result
            
            response = lambda_handler(mock_api_gateway_event, mock_lambda_context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['cache_hit'] is True
            assert body['sentiment'] == 'POSITIVE'
            assert body['score'] == 0.95


class TestAsyncHandlerIntegration:
    """Integration tests for async handler."""
    
    @pytest.mark.integration
    def test_async_handler_full_workflow(self, mock_aws_services, mock_lambda_context, mock_async_api_gateway_event):
        """Test complete async handler workflow."""
        from src.handlers.async_handler import lambda_handler
        
        with patch('src.handlers.async_handler._store_job_data') as mock_store_job:
            mock_store_job.return_value = True
            
            with patch('src.handlers.async_handler._store_document') as mock_store_doc:
                mock_store_doc.return_value = True
                
                with patch('src.handlers.async_handler._start_step_function') as mock_start_sf:
                    mock_start_sf.return_value = True
                    
                    response = lambda_handler(mock_async_api_gateway_event, mock_lambda_context)
                    
                    assert response['statusCode'] == 202
                    body = json.loads(response['body'])
                    assert body['status'] == 'PROCESSING'
                    assert 'job_id' in body
                    assert 'estimated_completion' in body
    
    @pytest.mark.integration
    def test_async_handler_job_storage_failure(self, mock_aws_services, mock_lambda_context, mock_async_api_gateway_event):
        """Test async handler with job storage failure."""
        from src.handlers.async_handler import lambda_handler
        
        with patch('src.handlers.async_handler._store_job_data') as mock_store_job:
            mock_store_job.return_value = False
            
            response = lambda_handler(mock_async_api_gateway_event, mock_lambda_context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['error']['code'] == 'INTERNAL_ERROR'
    
    @pytest.mark.integration
    def test_async_handler_document_storage_failure(self, mock_aws_services, mock_lambda_context, mock_async_api_gateway_event):
        """Test async handler with document storage failure."""
        from src.handlers.async_handler import lambda_handler
        
        with patch('src.handlers.async_handler._store_job_data') as mock_store_job:
            mock_store_job.return_value = True
            
            with patch('src.handlers.async_handler._store_document') as mock_store_doc:
                mock_store_doc.return_value = False
                
                response = lambda_handler(mock_async_api_gateway_event, mock_lambda_context)
                
                assert response['statusCode'] == 500
                body = json.loads(response['body'])
                assert body['error']['code'] == 'INTERNAL_ERROR'
    
    @pytest.mark.integration
    def test_async_handler_step_function_failure(self, mock_aws_services, mock_lambda_context, mock_async_api_gateway_event):
        """Test async handler with Step Function failure."""
        from src.handlers.async_handler import lambda_handler
        
        with patch('src.handlers.async_handler._store_job_data') as mock_store_job:
            mock_store_job.return_value = True
            
            with patch('src.handlers.async_handler._store_document') as mock_store_doc:
                mock_store_doc.return_value = True
                
                with patch('src.handlers.async_handler._start_step_function') as mock_start_sf:
                    mock_start_sf.return_value = False
                    
                    response = lambda_handler(mock_async_api_gateway_event, mock_lambda_context)
                    
                    assert response['statusCode'] == 500
                    body = json.loads(response['body'])
                    assert body['error']['code'] == 'INTERNAL_ERROR'


class TestStatusHandlerIntegration:
    """Integration tests for status handler."""
    
    @pytest.mark.integration
    def test_status_handler_success(self, mock_aws_services, mock_lambda_context, mock_status_api_gateway_event):
        """Test status handler successful retrieval."""
        from src.handlers.status_handler import lambda_handler
        
        with patch('src.handlers.status_handler._get_job_status') as mock_get_status:
            mock_get_status.return_value = sample_job_data
            
            response = lambda_handler(mock_status_api_gateway_event, mock_lambda_context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['job_id'] == 'test-job-123'
            assert body['status'] == 'PROCESSING'
    
    @pytest.mark.integration
    def test_status_handler_job_not_found(self, mock_aws_services, mock_lambda_context, mock_status_api_gateway_event):
        """Test status handler with job not found."""
        from src.handlers.status_handler import lambda_handler
        
        with patch('src.handlers.status_handler._get_job_status') as mock_get_status:
            mock_get_status.return_value = None
            
            response = lambda_handler(mock_status_api_gateway_event, mock_lambda_context)
            
            assert response['statusCode'] == 404
            body = json.loads(response['body'])
            assert body['error']['code'] == 'JOB_NOT_FOUND'
    
    @pytest.mark.integration
    def test_status_handler_database_error(self, mock_aws_services, mock_lambda_context, mock_status_api_gateway_event):
        """Test status handler with database error."""
        from src.handlers.status_handler import lambda_handler
        
        with patch('src.handlers.status_handler._get_job_status') as mock_get_status:
            mock_get_status.side_effect = Exception("Database error")
            
            response = lambda_handler(mock_status_api_gateway_event, mock_lambda_context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['error']['code'] == 'INTERNAL_ERROR'


class TestHealthHandlerIntegration:
    """Integration tests for health handler."""
    
    @pytest.mark.integration
    def test_health_handler_success(self, mock_aws_services, mock_lambda_context, mock_health_api_gateway_event):
        """Test health handler successful response."""
        from src.handlers.health_handler import lambda_handler
        
        response = lambda_handler(mock_health_api_gateway_event, mock_lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'healthy'
        assert 'version' in body
        assert 'timestamp' in body
    
    @pytest.mark.integration
    def test_health_handler_with_aws_services(self, mock_aws_services, mock_lambda_context, mock_health_api_gateway_event):
        """Test health handler with AWS service checks."""
        from src.handlers.health_handler import lambda_handler
        
        # Mock AWS service responses
        with patch('src.handlers.health_handler.aws_clients') as mock_aws:
            mock_aws.dynamodb.describe_table.return_value = {'Table': {'TableStatus': 'ACTIVE'}}
            mock_aws.s3.head_bucket.return_value = {}
            mock_aws.comprehend.describe_endpoint.return_value = {'EndpointProperties': {'Status': 'IN_SERVICE'}}
            
            response = lambda_handler(mock_health_api_gateway_event, mock_lambda_context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['status'] == 'healthy'
            assert 'aws_services' in body
            assert body['aws_services']['dynamodb'] == 'healthy'
            assert body['aws_services']['s3'] == 'healthy'
            assert body['aws_services']['comprehend'] == 'healthy'
