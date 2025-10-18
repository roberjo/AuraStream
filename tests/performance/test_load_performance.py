"""Load testing for AuraStream API endpoints."""

import pytest
import json
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from moto import mock_dynamodb, mock_s3, mock_comprehend
import boto3
from unittest.mock import patch

from src.handlers.sync_handler import lambda_handler as sync_handler
from src.handlers.async_handler import lambda_handler as async_handler
from src.handlers.status_handler import lambda_handler as status_handler


class TestLoadPerformance:
    """Load testing for API endpoints."""
    
    @pytest.fixture
    def mock_aws_services(self):
        """Mock AWS services for load testing."""
        with mock_dynamodb(), mock_s3(), mock_comprehend():
            # Set up DynamoDB tables
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            
            cache_table = dynamodb.create_table(
                TableName='test-sentiment-cache',
                KeySchema=[{'AttributeName': 'text_hash', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'text_hash', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            
            job_table = dynamodb.create_table(
                TableName='test-job-results',
                KeySchema=[{'AttributeName': 'job_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'job_id', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Create S3 bucket
            s3 = boto3.client('s3', region_name='us-east-1')
            s3.create_bucket(Bucket='test-aurastream-documents')
            
            yield {
                'cache_table': cache_table,
                'job_table': job_table,
                's3': s3
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
    def test_sync_endpoint_load(self, mock_analyze, mock_aws_services, lambda_context):
        """Test sync endpoint under load."""
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
        
        # Test data
        test_texts = [
            'I love this product!',
            'This is amazing!',
            'Great quality and fast delivery.',
            'Highly recommended!',
            'Excellent customer service.'
        ]
        
        # Load test parameters
        num_requests = 100
        max_workers = 10
        
        def make_request(text):
            """Make a single request."""
            event = {
                'httpMethod': 'POST',
                'path': '/analyze/sync',
                'body': json.dumps({
                    'text': text,
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
                    'requestId': f'test-request-{time.time()}'
                }
            }
            
            start_time = time.time()
            response = sync_handler(event, lambda_context)
            end_time = time.time()
            
            return {
                'status_code': response['statusCode'],
                'response_time': end_time - start_time,
                'success': response['statusCode'] == 200
            }
        
        # Execute load test
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i in range(num_requests):
                text = test_texts[i % len(test_texts)]
                future = executor.submit(make_request, text)
                futures.append(future)
            
            results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = sum(1 for r in results if r['success'])
        failed_requests = num_requests - successful_requests
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        max_response_time = max(r['response_time'] for r in results)
        min_response_time = min(r['response_time'] for r in results)
        requests_per_second = num_requests / total_time
        
        # Performance assertions
        assert successful_requests >= num_requests * 0.95, f"Success rate too low: {successful_requests/num_requests*100:.1f}%"
        assert avg_response_time < 1.0, f"Average response time too high: {avg_response_time:.3f}s"
        assert max_response_time < 2.0, f"Max response time too high: {max_response_time:.3f}s"
        assert requests_per_second > 50, f"Throughput too low: {requests_per_second:.1f} RPS"
        
        print(f"Load Test Results:")
        print(f"  Total Requests: {num_requests}")
        print(f"  Successful: {successful_requests}")
        print(f"  Failed: {failed_requests}")
        print(f"  Success Rate: {successful_requests/num_requests*100:.1f}%")
        print(f"  Average Response Time: {avg_response_time:.3f}s")
        print(f"  Max Response Time: {max_response_time:.3f}s")
        print(f"  Min Response Time: {min_response_time:.3f}s")
        print(f"  Requests Per Second: {requests_per_second:.1f}")
        print(f"  Total Time: {total_time:.3f}s")
    
    def test_async_endpoint_load(self, mock_aws_services, lambda_context):
        """Test async endpoint under load."""
        # Set environment variables
        import os
        os.environ['JOB_RESULTS_TABLE'] = 'test-job-results'
        os.environ['DOCUMENTS_BUCKET'] = 'test-aurastream-documents'
        os.environ['STEP_FUNCTION_ARN'] = 'arn:aws:states:us-east-1:123456789012:stateMachine:test'
        
        # Test data
        test_texts = [
            'This is a longer text for async processing. ' * 50,
            'Another long text for testing async capabilities. ' * 50,
            'Yet another text to test the async endpoint. ' * 50,
            'More text for comprehensive async testing. ' * 50,
            'Final text for async load testing. ' * 50
        ]
        
        # Load test parameters
        num_requests = 50
        max_workers = 5
        
        def make_request(text, index):
            """Make a single async request."""
            event = {
                'httpMethod': 'POST',
                'path': '/analyze/async',
                'body': json.dumps({
                    'text': text,
                    'source_id': f'test-source-{index}',
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
                    'requestId': f'test-request-{time.time()}-{index}'
                }
            }
            
            start_time = time.time()
            response = async_handler(event, lambda_context)
            end_time = time.time()
            
            return {
                'status_code': response['statusCode'],
                'response_time': end_time - start_time,
                'success': response['statusCode'] == 202,
                'job_id': json.loads(response['body']).get('job_id') if response['statusCode'] == 202 else None
            }
        
        # Execute load test
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i in range(num_requests):
                text = test_texts[i % len(test_texts)]
                future = executor.submit(make_request, text, i)
                futures.append(future)
            
            results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = sum(1 for r in results if r['success'])
        failed_requests = num_requests - successful_requests
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        max_response_time = max(r['response_time'] for r in results)
        requests_per_second = num_requests / total_time
        
        # Performance assertions
        assert successful_requests >= num_requests * 0.95, f"Success rate too low: {successful_requests/num_requests*100:.1f}%"
        assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time:.3f}s"
        assert max_response_time < 5.0, f"Max response time too high: {max_response_time:.3f}s"
        assert requests_per_second > 20, f"Throughput too low: {requests_per_second:.1f} RPS"
        
        print(f"Async Load Test Results:")
        print(f"  Total Requests: {num_requests}")
        print(f"  Successful: {successful_requests}")
        print(f"  Failed: {failed_requests}")
        print(f"  Success Rate: {successful_requests/num_requests*100:.1f}%")
        print(f"  Average Response Time: {avg_response_time:.3f}s")
        print(f"  Max Response Time: {max_response_time:.3f}s")
        print(f"  Requests Per Second: {requests_per_second:.1f}")
        print(f"  Total Time: {total_time:.3f}s")
    
    def test_cache_performance(self, mock_aws_services, lambda_context):
        """Test cache performance under load."""
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
            
            # Test cache performance with repeated requests
            test_text = 'I love this product!'
            num_requests = 100
            
            def make_request():
                """Make a single request."""
                event = {
                    'httpMethod': 'POST',
                    'path': '/analyze/sync',
                    'body': json.dumps({
                        'text': test_text,
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
                        'requestId': f'test-request-{time.time()}'
                    }
                }
                
                start_time = time.time()
                response = sync_handler(event, lambda_context)
                end_time = time.time()
                
                body = json.loads(response['body'])
                return {
                    'response_time': end_time - start_time,
                    'cache_hit': body.get('cache_hit', False),
                    'success': response['statusCode'] == 200
                }
            
            # Execute requests
            results = [make_request() for _ in range(num_requests)]
            
            # Analyze cache performance
            cache_hits = sum(1 for r in results if r['cache_hit'])
            cache_misses = num_requests - cache_hits
            cache_hit_rate = cache_hits / num_requests
            
            # Calculate response times for cache hits vs misses
            cache_hit_times = [r['response_time'] for r in results if r['cache_hit']]
            cache_miss_times = [r['response_time'] for r in results if not r['cache_hit']]
            
            avg_cache_hit_time = sum(cache_hit_times) / len(cache_hit_times) if cache_hit_times else 0
            avg_cache_miss_time = sum(cache_miss_times) / len(cache_miss_times) if cache_miss_times else 0
            
            # Performance assertions
            assert cache_hit_rate > 0.9, f"Cache hit rate too low: {cache_hit_rate*100:.1f}%"
            assert avg_cache_hit_time < avg_cache_miss_time, "Cache hits should be faster than misses"
            assert avg_cache_hit_time < 0.1, f"Cache hit response time too high: {avg_cache_hit_time:.3f}s"
            
            print(f"Cache Performance Results:")
            print(f"  Total Requests: {num_requests}")
            print(f"  Cache Hits: {cache_hits}")
            print(f"  Cache Misses: {cache_misses}")
            print(f"  Cache Hit Rate: {cache_hit_rate*100:.1f}%")
            print(f"  Avg Cache Hit Time: {avg_cache_hit_time:.3f}s")
            print(f"  Avg Cache Miss Time: {avg_cache_miss_time:.3f}s")
            print(f"  Performance Improvement: {(avg_cache_miss_time - avg_cache_hit_time) / avg_cache_miss_time * 100:.1f}%")
    
    def test_concurrent_requests(self, mock_aws_services, lambda_context):
        """Test concurrent request handling."""
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
            
            # Test concurrent requests
            num_concurrent = 20
            test_texts = [f'Test text {i}' for i in range(num_concurrent)]
            
            def make_request(text, index):
                """Make a single request."""
                event = {
                    'httpMethod': 'POST',
                    'path': '/analyze/sync',
                    'body': json.dumps({
                        'text': text,
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
                        'requestId': f'test-request-{index}'
                    }
                }
                
                start_time = time.time()
                response = sync_handler(event, lambda_context)
                end_time = time.time()
                
                return {
                    'index': index,
                    'status_code': response['statusCode'],
                    'response_time': end_time - start_time,
                    'success': response['statusCode'] == 200
                }
            
            # Execute concurrent requests
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                futures = [executor.submit(make_request, text, i) for i, text in enumerate(test_texts)]
                results = [future.result() for future in futures]
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful_requests = sum(1 for r in results if r['success'])
            avg_response_time = sum(r['response_time'] for r in results) / len(results)
            max_response_time = max(r['response_time'] for r in results)
            
            # Performance assertions
            assert successful_requests == num_concurrent, f"Not all concurrent requests succeeded: {successful_requests}/{num_concurrent}"
            assert avg_response_time < 1.0, f"Average response time too high: {avg_response_time:.3f}s"
            assert max_response_time < 2.0, f"Max response time too high: {max_response_time:.3f}s"
            
            print(f"Concurrent Request Results:")
            print(f"  Concurrent Requests: {num_concurrent}")
            print(f"  Successful: {successful_requests}")
            print(f"  Average Response Time: {avg_response_time:.3f}s")
            print(f"  Max Response Time: {max_response_time:.3f}s")
            print(f"  Total Time: {total_time:.3f}s")
