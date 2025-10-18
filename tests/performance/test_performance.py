"""Performance tests for AuraStream API."""

import pytest
import time
import json
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from tests.fixtures.aws_fixtures import (
    mock_aws_services,
    mock_lambda_context,
    mock_api_gateway_event,
    mock_async_api_gateway_event
)


class TestSyncHandlerPerformance:
    """Performance tests for sync handler."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_sync_handler_response_time(self, mock_aws_services, mock_lambda_context, mock_api_gateway_event):
        """Test sync handler response time under normal load."""
        from src.handlers.sync_handler import lambda_handler
        
        with pytest.mock.patch('src.handlers.sync_handler._analyze_sentiment') as mock_analyze:
            mock_analyze.return_value = {
                'Sentiment': 'POSITIVE',
                'SentimentScore': {'Positive': 0.95, 'Negative': 0.02, 'Neutral': 0.02, 'Mixed': 0.01},
                'LanguageCode': 'en'
            }
            
            with pytest.mock.patch('src.handlers.sync_handler.SentimentCache') as mock_cache:
                mock_cache.return_value.get_cached_result.return_value = None
                mock_cache.return_value.store_result.return_value = True
                
                with pytest.mock.patch('src.handlers.sync_handler.PIIDetector') as mock_pii:
                    mock_pii.return_value.detect_pii.return_value = {'pii_detected': False}
                    
                    # Measure response time
                    start_time = time.time()
                    response = lambda_handler(mock_api_gateway_event, mock_lambda_context)
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    
                    assert response['statusCode'] == 200
                    assert response_time < 1000  # Should respond within 1 second
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_sync_handler_concurrent_requests(self, mock_aws_services, mock_lambda_context):
        """Test sync handler performance under concurrent load."""
        from src.handlers.sync_handler import lambda_handler
        
        def make_request():
            event = mock_api_gateway_event.copy()
            event['body'] = json.dumps({"text": f"Test text {time.time()}"})
            
            with pytest.mock.patch('src.handlers.sync_handler._analyze_sentiment') as mock_analyze:
                mock_analyze.return_value = {
                    'Sentiment': 'POSITIVE',
                    'SentimentScore': {'Positive': 0.95, 'Negative': 0.02, 'Neutral': 0.02, 'Mixed': 0.01},
                    'LanguageCode': 'en'
                }
                
                with pytest.mock.patch('src.handlers.sync_handler.SentimentCache') as mock_cache:
                    mock_cache.return_value.get_cached_result.return_value = None
                    mock_cache.return_value.store_result.return_value = True
                    
                    with pytest.mock.patch('src.handlers.sync_handler.PIIDetector') as mock_pii:
                        mock_pii.return_value.detect_pii.return_value = {'pii_detected': False}
                        
                        start_time = time.time()
                        response = lambda_handler(event, mock_lambda_context)
                        end_time = time.time()
                        
                        return {
                            'status_code': response['statusCode'],
                            'response_time': (end_time - start_time) * 1000
                        }
        
        # Run 10 concurrent requests
        num_requests = 10
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in futures]
        
        # Analyze results
        successful_requests = [r for r in results if r['status_code'] == 200]
        response_times = [r['response_time'] for r in successful_requests]
        
        assert len(successful_requests) == num_requests
        assert max(response_times) < 2000  # All requests should complete within 2 seconds
        assert sum(response_times) / len(response_times) < 1000  # Average should be under 1 second
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_sync_handler_large_text_performance(self, mock_aws_services, mock_lambda_context):
        """Test sync handler performance with large text."""
        from src.handlers.sync_handler import lambda_handler
        
        # Create large text (close to limit)
        large_text = "This is a test sentence. " * 40000  # ~1MB
        
        event = mock_api_gateway_event.copy()
        event['body'] = json.dumps({"text": large_text})
        
        with pytest.mock.patch('src.handlers.sync_handler._analyze_sentiment') as mock_analyze:
            mock_analyze.return_value = {
                'Sentiment': 'POSITIVE',
                'SentimentScore': {'Positive': 0.95, 'Negative': 0.02, 'Neutral': 0.02, 'Mixed': 0.01},
                'LanguageCode': 'en'
            }
            
            with pytest.mock.patch('src.handlers.sync_handler.SentimentCache') as mock_cache:
                mock_cache.return_value.get_cached_result.return_value = None
                mock_cache.return_value.store_result.return_value = True
                
                with pytest.mock.patch('src.handlers.sync_handler.PIIDetector') as mock_pii:
                    mock_pii.return_value.detect_pii.return_value = {'pii_detected': False}
                    
                    start_time = time.time()
                    response = lambda_handler(event, mock_lambda_context)
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000
                    
                    assert response['statusCode'] == 200
                    assert response_time < 5000  # Should handle large text within 5 seconds


class TestAsyncHandlerPerformance:
    """Performance tests for async handler."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_async_handler_response_time(self, mock_aws_services, mock_lambda_context, mock_async_api_gateway_event):
        """Test async handler response time."""
        from src.handlers.async_handler import lambda_handler
        
        with pytest.mock.patch('src.handlers.async_handler._store_job_data') as mock_store_job:
            mock_store_job.return_value = True
            
            with pytest.mock.patch('src.handlers.async_handler._store_document') as mock_store_doc:
                mock_store_doc.return_value = True
                
                with pytest.mock.patch('src.handlers.async_handler._start_step_function') as mock_start_sf:
                    mock_start_sf.return_value = True
                    
                    start_time = time.time()
                    response = lambda_handler(mock_async_api_gateway_event, mock_lambda_context)
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000
                    
                    assert response['statusCode'] == 202
                    assert response_time < 2000  # Should respond within 2 seconds
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_async_handler_concurrent_submissions(self, mock_aws_services, mock_lambda_context):
        """Test async handler performance under concurrent load."""
        from src.handlers.async_handler import lambda_handler
        
        def make_request():
            event = mock_async_api_gateway_event.copy()
            event['body'] = json.dumps({
                "text": f"Test text {time.time()}",
                "source_id": f"test-source-{time.time()}"
            })
            
            with pytest.mock.patch('src.handlers.async_handler._store_job_data') as mock_store_job:
                mock_store_job.return_value = True
                
                with pytest.mock.patch('src.handlers.async_handler._store_document') as mock_store_doc:
                    mock_store_doc.return_value = True
                    
                    with pytest.mock.patch('src.handlers.async_handler._start_step_function') as mock_start_sf:
                        mock_start_sf.return_value = True
                        
                        start_time = time.time()
                        response = lambda_handler(event, mock_lambda_context)
                        end_time = time.time()
                        
                        return {
                            'status_code': response['statusCode'],
                            'response_time': (end_time - start_time) * 1000
                        }
        
        # Run 5 concurrent requests (async handler is more resource intensive)
        num_requests = 5
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in futures]
        
        # Analyze results
        successful_requests = [r for r in results if r['status_code'] == 202]
        response_times = [r['response_time'] for r in successful_requests]
        
        assert len(successful_requests) == num_requests
        assert max(response_times) < 3000  # All requests should complete within 3 seconds
        assert sum(response_times) / len(response_times) < 2000  # Average should be under 2 seconds


class TestCachePerformance:
    """Performance tests for cache operations."""
    
    @pytest.mark.performance
    def test_cache_hit_performance(self, mock_aws_services):
        """Test cache hit performance."""
        from src.cache.sentiment_cache import SentimentCache
        
        cache = SentimentCache()
        cached_result = {
            'sentiment': 'POSITIVE',
            'score': 0.95,
            'language_code': 'en'
        }
        
        with pytest.mock.patch('src.cache.sentiment_cache.aws_clients') as mock_aws:
            mock_table = pytest.mock.Mock()
            mock_aws.dynamodb.Table.return_value = mock_table
            mock_table.get_item.return_value = {
                'Item': {
                    'text_hash': 'test-hash',
                    'result': json.dumps(cached_result),
                    'ttl': int(time.time()) + 3600
                }
            }
            
            start_time = time.time()
            result = cache.get_cached_result("test text")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            assert result == cached_result
            assert response_time < 100  # Cache hit should be very fast
    
    @pytest.mark.performance
    def test_cache_store_performance(self, mock_aws_services):
        """Test cache store performance."""
        from src.cache.sentiment_cache import SentimentCache
        
        cache = SentimentCache()
        result_data = {
            'sentiment': 'POSITIVE',
            'score': 0.95,
            'language_code': 'en'
        }
        
        with pytest.mock.patch('src.cache.sentiment_cache.aws_clients') as mock_aws:
            mock_table = pytest.mock.Mock()
            mock_aws.dynamodb.Table.return_value = mock_table
            mock_table.put_item.return_value = {}
            
            start_time = time.time()
            result = cache.store_result("test text", result_data)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            assert result is True
            assert response_time < 500  # Cache store should be reasonably fast


class TestMemoryUsage:
    """Memory usage tests."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_large_text(self, mock_aws_services, mock_lambda_context):
        """Test memory usage with large text processing."""
        import psutil
        import os
        
        from src.handlers.sync_handler import lambda_handler
        
        # Get current process
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large text
        large_text = "This is a test sentence. " * 50000  # ~1.25MB
        
        event = mock_api_gateway_event.copy()
        event['body'] = json.dumps({"text": large_text})
        
        with pytest.mock.patch('src.handlers.sync_handler._analyze_sentiment') as mock_analyze:
            mock_analyze.return_value = {
                'Sentiment': 'POSITIVE',
                'SentimentScore': {'Positive': 0.95, 'Negative': 0.02, 'Neutral': 0.02, 'Mixed': 0.01},
                'LanguageCode': 'en'
            }
            
            with pytest.mock.patch('src.handlers.sync_handler.SentimentCache') as mock_cache:
                mock_cache.return_value.get_cached_result.return_value = None
                mock_cache.return_value.store_result.return_value = True
                
                with pytest.mock.patch('src.handlers.sync_handler.PIIDetector') as mock_pii:
                    mock_pii.return_value.detect_pii.return_value = {'pii_detected': False}
                    
                    response = lambda_handler(event, mock_lambda_context)
                    
                    final_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_increase = final_memory - initial_memory
                    
                    assert response['statusCode'] == 200
                    assert memory_increase < 100  # Should not increase memory by more than 100MB
