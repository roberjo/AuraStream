# AuraStream Testing Strategy & Quality Assurance Guide

## Table of Contents
1. [Testing Overview](#testing-overview)
2. [Testing Strategy](#testing-strategy)
3. [Test Types and Levels](#test-types-and-levels)
4. [Test Automation Framework](#test-automation-framework)
5. [Unit Testing](#unit-testing)
6. [Integration Testing](#integration-testing)
7. [End-to-End Testing](#end-to-end-testing)
8. [Performance Testing](#performance-testing)
9. [Security Testing](#security-testing)
10. [Test Data Management](#test-data-management)
11. [CI/CD Integration](#cicd-integration)
12. [Quality Metrics](#quality-metrics)

---

## Testing Overview

### Testing Philosophy

AuraStream follows a **comprehensive testing strategy** that ensures high-quality, reliable, and secure software delivery. Our testing approach is based on the **Testing Pyramid** model, emphasizing automated testing at all levels with a focus on fast feedback and continuous quality improvement.

### Testing Principles

1. **Test Early and Often**: Testing begins in the design phase and continues throughout development
2. **Automation First**: Automate all repetitive and regression tests
3. **Risk-Based Testing**: Focus testing efforts on high-risk areas
4. **Continuous Testing**: Integrate testing into the CI/CD pipeline
5. **Quality Gates**: Implement quality gates to prevent low-quality code from reaching production
6. **Test-Driven Development**: Write tests before implementing features
7. **Comprehensive Coverage**: Achieve high test coverage across all components

### Testing Objectives

#### Primary Goals
- **Quality Assurance**: Ensure software meets functional and non-functional requirements
- **Risk Mitigation**: Identify and mitigate potential issues before production
- **Regression Prevention**: Prevent new changes from breaking existing functionality
- **Performance Validation**: Ensure system meets performance requirements
- **Security Validation**: Verify security controls and compliance requirements

#### Success Metrics
- **Test Coverage**: > 80% code coverage
- **Test Execution Time**: < 10 minutes for full test suite
- **Defect Detection Rate**: > 95% of defects caught before production
- **Test Automation**: > 90% of tests automated
- **Mean Time to Recovery**: < 30 minutes for critical issues

---

## Testing Strategy

### Testing Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │  ← Few, Slow, Expensive
                    │   (10%)         │
                    └─────────────────┘
                ┌─────────────────────────┐
                │   Integration Tests     │  ← Some, Medium Speed
                │        (20%)            │
                └─────────────────────────┘
        ┌─────────────────────────────────────────┐
        │           Unit Tests                    │  ← Many, Fast, Cheap
        │              (70%)                      │
        └─────────────────────────────────────────┘
```

### Testing Strategy Matrix

| Test Type | Frequency | Execution Time | Coverage | Purpose |
|-----------|-----------|----------------|----------|---------|
| **Unit Tests** | Every commit | < 2 minutes | 80%+ | Function correctness |
| **Integration Tests** | Every PR | < 5 minutes | 60%+ | Component interaction |
| **E2E Tests** | Daily | < 15 minutes | 40%+ | User journey validation |
| **Performance Tests** | Weekly | < 30 minutes | Key scenarios | Performance validation |
| **Security Tests** | Every PR | < 10 minutes | Security controls | Security validation |

### Test Environment Strategy

#### Environment Types

```python
# Test environment configuration
TEST_ENVIRONMENTS = {
    'local': {
        'purpose': 'Developer testing',
        'data': 'Mock data',
        'services': 'LocalStack, Docker',
        'access': 'Developers only'
    },
    'dev': {
        'purpose': 'Feature development',
        'data': 'Synthetic data',
        'services': 'AWS Dev',
        'access': 'Development team'
    },
    'staging': {
        'purpose': 'Pre-production testing',
        'data': 'Production-like data',
        'services': 'AWS Staging',
        'access': 'QA team, stakeholders'
    },
    'production': {
        'purpose': 'Live system',
        'data': 'Real customer data',
        'services': 'AWS Production',
        'access': 'Operations team'
    }
}
```

---

## Test Types and Levels

### 1. Unit Testing

#### Purpose and Scope
Unit tests verify the correctness of individual functions, methods, and classes in isolation. They are the foundation of our testing strategy and provide fast feedback during development.

#### Unit Test Structure

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.handlers.sync_handler import SyncHandler
from src.models.request_models import SentimentAnalysisRequest
from src.models.response_models import SentimentAnalysisResponse

class TestSyncHandler:
    """Test suite for SyncHandler class."""
    
    def setup_method(self):
        """Setup test fixtures before each test method."""
        self.handler = SyncHandler()
        self.sample_request = SentimentAnalysisRequest(
            text="I love this product!",
            options={"language_code": "en", "include_confidence": True}
        )
    
    def test_successful_sentiment_analysis(self):
        """Test successful sentiment analysis."""
        # Arrange
        expected_response = SentimentAnalysisResponse(
            sentiment="POSITIVE",
            score=0.95,
            language_code="en",
            confidence=0.98
        )
        
        with patch.object(self.handler, '_call_comprehend_api') as mock_comprehend:
            mock_comprehend.return_value = expected_response
            
            # Act
            result = self.handler.analyze_sentiment(self.sample_request)
            
            # Assert
            assert result.sentiment == "POSITIVE"
            assert result.score == 0.95
            assert result.confidence == 0.98
            mock_comprehend.assert_called_once_with(self.sample_request.text, self.sample_request.options)
    
    def test_invalid_text_validation(self):
        """Test validation of invalid text input."""
        # Arrange
        invalid_request = SentimentAnalysisRequest(
            text="",  # Empty text
            options={}
        )
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            self.handler.analyze_sentiment(invalid_request)
        
        assert "Text cannot be empty" in str(exc_info.value)
    
    def test_text_length_validation(self):
        """Test validation of text length limits."""
        # Arrange
        long_text = "x" * 5001  # Exceeds 5000 character limit
        invalid_request = SentimentAnalysisRequest(
            text=long_text,
            options={}
        )
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            self.handler.analyze_sentiment(invalid_request)
        
        assert "Text exceeds maximum length" in str(exc_info.value)
    
    def test_comprehend_api_failure(self):
        """Test handling of Comprehend API failures."""
        # Arrange
        with patch.object(self.handler, '_call_comprehend_api') as mock_comprehend:
            mock_comprehend.side_effect = ComprehendAPIError("API rate limit exceeded")
            
            # Act & Assert
            with pytest.raises(ServiceError) as exc_info:
                self.handler.analyze_sentiment(self.sample_request)
            
            assert "API rate limit exceeded" in str(exc_info.value)
    
    def test_cache_hit_scenario(self):
        """Test cache hit scenario."""
        # Arrange
        cached_response = SentimentAnalysisResponse(
            sentiment="POSITIVE",
            score=0.95,
            language_code="en",
            confidence=0.98
        )
        
        with patch.object(self.handler, '_get_cached_result') as mock_cache:
            mock_cache.return_value = cached_response
            
            # Act
            result = self.handler.analyze_sentiment(self.sample_request)
            
            # Assert
            assert result.sentiment == "POSITIVE"
            mock_cache.assert_called_once()
    
    def test_cache_miss_scenario(self):
        """Test cache miss scenario."""
        # Arrange
        with patch.object(self.handler, '_get_cached_result') as mock_cache:
            mock_cache.return_value = None
            
            with patch.object(self.handler, '_call_comprehend_api') as mock_comprehend:
                mock_comprehend.return_value = SentimentAnalysisResponse(
                    sentiment="POSITIVE",
                    score=0.95,
                    language_code="en",
                    confidence=0.98
                )
                
                # Act
                result = self.handler.analyze_sentiment(self.sample_request)
                
                # Assert
                assert result.sentiment == "POSITIVE"
                mock_cache.assert_called_once()
                mock_comprehend.assert_called_once()
```

#### Unit Test Best Practices

```python
class UnitTestBestPractices:
    """Examples of unit testing best practices."""
    
    def test_with_fixtures(self):
        """Use pytest fixtures for test data."""
        # Use fixtures for common test data
        pass
    
    def test_with_parametrize(self):
        """Use parametrize for testing multiple scenarios."""
        # Test multiple input/output combinations
        pass
    
    def test_with_mocking(self):
        """Use mocking to isolate units under test."""
        # Mock external dependencies
        pass
    
    def test_error_conditions(self):
        """Test error conditions and edge cases."""
        # Test exception handling
        pass
    
    def test_async_functions(self):
        """Test asynchronous functions properly."""
        # Use pytest-asyncio for async tests
        pass

# Example of parametrized tests
@pytest.mark.parametrize("input_text,expected_sentiment", [
    ("I love this product!", "POSITIVE"),
    ("This is terrible!", "NEGATIVE"),
    ("The weather is okay.", "NEUTRAL"),
    ("I have mixed feelings.", "MIXED")
])
def test_sentiment_classification(input_text, expected_sentiment):
    """Test sentiment classification with various inputs."""
    handler = SyncHandler()
    request = SentimentAnalysisRequest(text=input_text)
    
    with patch.object(handler, '_call_comprehend_api') as mock_comprehend:
        mock_comprehend.return_value = SentimentAnalysisResponse(
            sentiment=expected_sentiment,
            score=0.9,
            language_code="en",
            confidence=0.95
        )
        
        result = handler.analyze_sentiment(request)
        assert result.sentiment == expected_sentiment
```

### 2. Integration Testing

#### Purpose and Scope
Integration tests verify that different components work together correctly. They test the interaction between modules, services, and external dependencies.

#### Integration Test Structure

```python
import pytest
import boto3
from moto import mock_dynamodb, mock_s3, mock_comprehend
from src.handlers.sync_handler import SyncHandler
from src.cache.sentiment_cache import SentimentCache

class TestSyncHandlerIntegration:
    """Integration tests for SyncHandler."""
    
    @mock_dynamodb
    def test_dynamodb_integration(self):
        """Test integration with DynamoDB."""
        # Arrange
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-sentiment-cache',
            KeySchema=[{'AttributeName': 'text_hash', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'text_hash', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        cache = SentimentCache()
        handler = SyncHandler(cache=cache)
        
        # Act
        request = SentimentAnalysisRequest(text="Test message")
        result = handler.analyze_sentiment(request)
        
        # Assert
        assert result is not None
        # Verify data was stored in DynamoDB
        response = table.get_item(Key={'text_hash': 'test_hash'})
        assert 'Item' in response
    
    @mock_comprehend
    def test_comprehend_integration(self):
        """Test integration with Amazon Comprehend."""
        # Arrange
        handler = SyncHandler()
        request = SentimentAnalysisRequest(text="I love this product!")
        
        # Act
        result = handler.analyze_sentiment(request)
        
        # Assert
        assert result.sentiment in ["POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED"]
        assert 0.0 <= result.score <= 1.0
        assert 0.0 <= result.confidence <= 1.0
    
    def test_api_gateway_integration(self):
        """Test integration with API Gateway."""
        # Arrange
        event = {
            'httpMethod': 'POST',
            'path': '/analyze/sync',
            'body': '{"text": "I love this product!"}',
            'headers': {
                'Content-Type': 'application/json',
                'X-API-Key': 'test-api-key'
            }
        }
        
        # Act
        from src.handlers.sync_handler import lambda_handler
        response = lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'sentiment' in body
        assert 'score' in body
    
    def test_error_handling_integration(self):
        """Test error handling across components."""
        # Arrange
        event = {
            'httpMethod': 'POST',
            'path': '/analyze/sync',
            'body': '{"text": ""}',  # Invalid input
            'headers': {
                'Content-Type': 'application/json',
                'X-API-Key': 'test-api-key'
            }
        }
        
        # Act
        from src.handlers.sync_handler import lambda_handler
        response = lambda_handler(event, {})
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
```

### 3. End-to-End Testing

#### Purpose and Scope
E2E tests verify complete user journeys and system workflows. They test the system from the user's perspective, ensuring all components work together correctly.

#### E2E Test Structure

```python
import pytest
import requests
import time
from typing import Dict, Any

class TestEndToEnd:
    """End-to-end tests for AuraStream API."""
    
    @pytest.fixture
    def api_base_url(self):
        """API base URL fixture."""
        return "https://staging-api.aurastream.com/v1"
    
    @pytest.fixture
    def api_headers(self):
        """API headers fixture."""
        return {
            'Content-Type': 'application/json',
            'X-API-Key': 'test-api-key'
        }
    
    def test_sync_sentiment_analysis_e2e(self, api_base_url, api_headers):
        """Test complete sync sentiment analysis workflow."""
        # Arrange
        payload = {
            "text": "I absolutely love this new product! It's amazing!",
            "options": {
                "language_code": "en",
                "include_confidence": True,
                "include_pii_detection": True
            }
        }
        
        # Act
        response = requests.post(
            f"{api_base_url}/analyze/sync",
            json=payload,
            headers=api_headers,
            timeout=30
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert 'sentiment' in data
        assert 'score' in data
        assert 'language_code' in data
        assert 'confidence' in data
        assert 'pii_detected' in data
        assert 'processing_time_ms' in data
        assert 'request_id' in data
        
        assert data['sentiment'] in ["POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED"]
        assert 0.0 <= data['score'] <= 1.0
        assert 0.0 <= data['confidence'] <= 1.0
        assert isinstance(data['pii_detected'], bool)
        assert data['processing_time_ms'] < 1000  # Should be fast
    
    def test_async_sentiment_analysis_e2e(self, api_base_url, api_headers):
        """Test complete async sentiment analysis workflow."""
        # Arrange
        payload = {
            "text": "This is a large document that needs sentiment analysis. " * 100,
            "source_id": "e2e_test_001",
            "options": {
                "language_code": "en",
                "callback_url": "https://webhook.site/test"
            }
        }
        
        # Act - Submit job
        response = requests.post(
            f"{api_base_url}/analyze/async",
            json=payload,
            headers=api_headers,
            timeout=30
        )
        
        # Assert - Job submission
        assert response.status_code == 202
        data = response.json()
        
        assert 'job_id' in data
        assert 'status' in data
        assert 'message' in data
        assert 'estimated_completion' in data
        
        job_id = data['job_id']
        assert data['status'] == "PENDING"
        
        # Act - Poll for completion
        max_attempts = 30  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            status_response = requests.get(
                f"{api_base_url}/status/{job_id}",
                headers=api_headers,
                timeout=30
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            if status_data['status'] == "COMPLETED":
                # Assert - Job completion
                assert 'result' in status_data
                assert 'completed_at' in status_data
                
                result = status_data['result']
                assert 'sentiment' in result
                assert 'score' in result
                break
            elif status_data['status'] == "FAILED":
                pytest.fail(f"Job failed: {status_data.get('error', 'Unknown error')}")
            
            time.sleep(10)  # Wait 10 seconds before next poll
            attempt += 1
        else:
            pytest.fail("Job did not complete within expected time")
    
    def test_error_handling_e2e(self, api_base_url, api_headers):
        """Test error handling in E2E scenarios."""
        # Test invalid API key
        invalid_headers = api_headers.copy()
        invalid_headers['X-API-Key'] = 'invalid-key'
        
        response = requests.post(
            f"{api_base_url}/analyze/sync",
            json={"text": "Test message"},
            headers=invalid_headers,
            timeout=30
        )
        
        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
        assert data['error']['code'] == 'UNAUTHORIZED'
        
        # Test invalid input
        response = requests.post(
            f"{api_base_url}/analyze/sync",
            json={"text": ""},  # Empty text
            headers=api_headers,
            timeout=30
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
    
    def test_rate_limiting_e2e(self, api_base_url, api_headers):
        """Test rate limiting functionality."""
        # Send multiple requests quickly
        responses = []
        for i in range(10):
            response = requests.post(
                f"{api_base_url}/analyze/sync",
                json={"text": f"Test message {i}"},
                headers=api_headers,
                timeout=30
            )
            responses.append(response)
        
        # Check if any requests were rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        if rate_limited:
            # Verify rate limit response format
            rate_limit_response = next(r for r in responses if r.status_code == 429)
            data = rate_limit_response.json()
            assert 'error' in data
            assert data['error']['code'] == 'RATE_LIMIT_EXCEEDED'
            assert 'retry_after' in data['error']
```

---

## Test Automation Framework

### Framework Architecture

```python
# Test framework configuration
import pytest
import os
from typing import Dict, Any

class TestFramework:
    """Main test framework class."""
    
    def __init__(self):
        self.config = self._load_config()
        self.test_data = self._load_test_data()
        self.reporters = self._setup_reporters()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load test configuration."""
        return {
            'base_url': os.getenv('TEST_BASE_URL', 'https://staging-api.aurastream.com'),
            'api_key': os.getenv('TEST_API_KEY', 'test-api-key'),
            'timeout': int(os.getenv('TEST_TIMEOUT', '30')),
            'retry_count': int(os.getenv('TEST_RETRY_COUNT', '3')),
            'parallel_workers': int(os.getenv('TEST_WORKERS', '4'))
        }
    
    def _load_test_data(self) -> Dict[str, Any]:
        """Load test data from files."""
        return {
            'sample_texts': self._load_json('test_data/sample_texts.json'),
            'test_customers': self._load_json('test_data/test_customers.json'),
            'error_scenarios': self._load_json('test_data/error_scenarios.json')
        }
    
    def _setup_reporters(self) -> list:
        """Setup test reporters."""
        return [
            'html',
            'json',
            'junit',
            'allure'
        ]

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

# Test fixtures
@pytest.fixture(scope="session")
def test_framework():
    """Test framework fixture."""
    return TestFramework()

@pytest.fixture
def api_client(test_framework):
    """API client fixture."""
    return APIClient(test_framework.config)

@pytest.fixture
def test_data(test_framework):
    """Test data fixture."""
    return test_framework.test_data
```

### Test Data Management

```python
class TestDataManager:
    """Manages test data for different test scenarios."""
    
    def __init__(self):
        self.test_data = {
            'sentiment_texts': {
                'positive': [
                    "I absolutely love this product!",
                    "This is amazing and wonderful!",
                    "Best purchase I've ever made!"
                ],
                'negative': [
                    "This product is terrible!",
                    "I hate this so much!",
                    "Worst experience ever!"
                ],
                'neutral': [
                    "The weather is okay today.",
                    "This is a standard product.",
                    "Nothing special about this."
                ],
                'mixed': [
                    "I love the design but hate the price.",
                    "Great features but poor customer service.",
                    "Good product but delivery was slow."
                ]
            },
            'pii_texts': {
                'email': "Contact me at john.doe@example.com",
                'phone': "Call me at (555) 123-4567",
                'ssn': "My SSN is 123-45-6789",
                'credit_card': "My card number is 4111-1111-1111-1111"
            },
            'edge_cases': {
                'empty': "",
                'whitespace': "   ",
                'unicode': "Hello 世界! 🌍",
                'special_chars': "!@#$%^&*()_+-=[]{}|;':\",./<>?",
                'very_long': "x" * 10000
            }
        }
    
    def get_sentiment_text(self, sentiment: str) -> str:
        """Get a sample text for the specified sentiment."""
        texts = self.test_data['sentiment_texts'].get(sentiment, [])
        return texts[0] if texts else "Sample text"
    
    def get_pii_text(self, pii_type: str) -> str:
        """Get a sample text containing PII."""
        return self.test_data['pii_texts'].get(pii_type, "No PII text")
    
    def get_edge_case_text(self, case: str) -> str:
        """Get a sample text for edge case testing."""
        return self.test_data['edge_cases'].get(case, "Normal text")

# Test data fixtures
@pytest.fixture
def sentiment_texts():
    """Fixture for sentiment test texts."""
    return TestDataManager().test_data['sentiment_texts']

@pytest.fixture
def pii_texts():
    """Fixture for PII test texts."""
    return TestDataManager().test_data['pii_texts']

@pytest.fixture
def edge_case_texts():
    """Fixture for edge case test texts."""
    return TestDataManager().test_data['edge_cases']
```

---

## Performance Testing

### Performance Test Framework

```python
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
import pytest

class PerformanceTestFramework:
    """Framework for performance testing."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.results = []
    
    async def load_test_sync_endpoint(self, concurrent_users: int, 
                                    requests_per_user: int) -> Dict[str, Any]:
        """
        Perform load test on sync endpoint.
        
        Args:
            concurrent_users: Number of concurrent users
            requests_per_user: Number of requests per user
            
        Returns:
            Performance test results
        """
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for user_id in range(concurrent_users):
                task = self._user_simulation(session, user_id, requests_per_user)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        # Aggregate results
        all_responses = []
        for user_results in results:
            all_responses.extend(user_results)
        
        return self._analyze_results(all_responses, end_time - start_time)
    
    async def _user_simulation(self, session: aiohttp.ClientSession, 
                             user_id: int, request_count: int) -> List[Dict]:
        """Simulate a single user making requests."""
        responses = []
        
        for request_id in range(request_count):
            payload = {
                "text": f"User {user_id} request {request_id} - I love this product!",
                "options": {"language_code": "en"}
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key
            }
            
            start_time = time.time()
            
            try:
                async with session.post(
                    f"{self.base_url}/analyze/sync",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # Convert to ms
                    
                    responses.append({
                        'user_id': user_id,
                        'request_id': request_id,
                        'status_code': response.status,
                        'response_time': response_time,
                        'success': response.status == 200
                    })
                    
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                responses.append({
                    'user_id': user_id,
                    'request_id': request_id,
                    'status_code': 0,
                    'response_time': response_time,
                    'success': False,
                    'error': str(e)
                })
        
        return responses
    
    def _analyze_results(self, responses: List[Dict], total_time: float) -> Dict[str, Any]:
        """Analyze performance test results."""
        successful_responses = [r for r in responses if r['success']]
        failed_responses = [r for r in responses if not r['success']]
        
        response_times = [r['response_time'] for r in successful_responses]
        
        return {
            'total_requests': len(responses),
            'successful_requests': len(successful_responses),
            'failed_requests': len(failed_responses),
            'success_rate': len(successful_responses) / len(responses) * 100,
            'total_time': total_time,
            'requests_per_second': len(responses) / total_time,
            'response_times': {
                'min': min(response_times) if response_times else 0,
                'max': max(response_times) if response_times else 0,
                'mean': statistics.mean(response_times) if response_times else 0,
                'median': statistics.median(response_times) if response_times else 0,
                'p95': self._percentile(response_times, 95),
                'p99': self._percentile(response_times, 99)
            },
            'error_breakdown': self._analyze_errors(failed_responses)
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _analyze_errors(self, failed_responses: List[Dict]) -> Dict[str, int]:
        """Analyze error types in failed responses."""
        error_counts = {}
        for response in failed_responses:
            status_code = response['status_code']
            error_counts[status_code] = error_counts.get(status_code, 0) + 1
        return error_counts

# Performance test cases
class TestPerformance:
    """Performance test cases."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_sync_endpoint_load(self):
        """Test sync endpoint under load."""
        framework = PerformanceTestFramework(
            base_url="https://staging-api.aurastream.com/v1",
            api_key="test-api-key"
        )
        
        # Test with 100 concurrent users, 10 requests each
        results = await framework.load_test_sync_endpoint(100, 10)
        
        # Assertions
        assert results['success_rate'] >= 95, f"Success rate too low: {results['success_rate']}%"
        assert results['response_times']['p99'] < 2000, f"P99 latency too high: {results['response_times']['p99']}ms"
        assert results['requests_per_second'] >= 100, f"Throughput too low: {results['requests_per_second']} RPS"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_sync_endpoint_stress(self):
        """Test sync endpoint under stress."""
        framework = PerformanceTestFramework(
            base_url="https://staging-api.aurastream.com/v1",
            api_key="test-api-key"
        )
        
        # Test with 500 concurrent users, 5 requests each
        results = await framework.load_test_sync_endpoint(500, 5)
        
        # Assertions
        assert results['success_rate'] >= 90, f"Success rate too low: {results['success_rate']}%"
        assert results['response_times']['p95'] < 5000, f"P95 latency too high: {results['response_times']['p95']}ms"
    
    @pytest.mark.performance
    def test_memory_usage(self):
        """Test memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        # ... test code ...
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Assert memory usage is reasonable
        assert memory_increase < 100, f"Memory usage increased too much: {memory_increase}MB"
```

### Performance Benchmarks

```python
class PerformanceBenchmarks:
    """Performance benchmarks and thresholds."""
    
    BENCHMARKS = {
        'sync_endpoint': {
            'response_time_p95': 1000,  # ms
            'response_time_p99': 2000,  # ms
            'throughput': 1000,  # requests per second
            'success_rate': 99.9,  # percentage
            'concurrent_users': 1000
        },
        'async_endpoint': {
            'job_creation_time': 500,  # ms
            'job_processing_time': 300000,  # ms (5 minutes)
            'success_rate': 99.5,  # percentage
            'concurrent_jobs': 100
        },
        'cache_performance': {
            'hit_rate': 60,  # percentage
            'cache_response_time': 50,  # ms
            'cache_miss_response_time': 1000  # ms
        }
    }
    
    @classmethod
    def validate_performance(cls, test_type: str, results: Dict[str, Any]) -> bool:
        """
        Validate performance test results against benchmarks.
        
        Args:
            test_type: Type of performance test
            results: Test results
            
        Returns:
            True if performance meets benchmarks
        """
        benchmarks = cls.BENCHMARKS.get(test_type, {})
        
        for metric, threshold in benchmarks.items():
            if metric in results:
                if results[metric] > threshold:
                    return False
        
        return True
```

---

## Security Testing

### Security Test Framework

```python
import requests
import pytest
from typing import List, Dict, Any

class SecurityTestFramework:
    """Framework for security testing."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.security_tests = {
            'injection': self._test_injection_attacks,
            'authentication': self._test_authentication,
            'authorization': self._test_authorization,
            'input_validation': self._test_input_validation,
            'rate_limiting': self._test_rate_limiting
        }
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run all security tests."""
        results = {}
        
        for test_name, test_func in self.security_tests.items():
            try:
                results[test_name] = test_func()
            except Exception as e:
                results[test_name] = {'status': 'error', 'message': str(e)}
        
        return results
    
    def _test_injection_attacks(self) -> Dict[str, Any]:
        """Test for injection attacks."""
        injection_payloads = [
            # SQL Injection
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            
            # XSS
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            
            # Command Injection
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`"
        ]
        
        results = []
        for payload in injection_payloads:
            response = self._send_request({"text": payload})
            results.append({
                'payload': payload,
                'status_code': response.status_code,
                'vulnerable': self._is_vulnerable(response)
            })
        
        return {
            'status': 'completed',
            'results': results,
            'vulnerabilities_found': sum(1 for r in results if r['vulnerable'])
        }
    
    def _test_authentication(self) -> Dict[str, Any]:
        """Test authentication mechanisms."""
        tests = [
            {
                'name': 'valid_api_key',
                'headers': {'X-API-Key': self.api_key},
                'expected_status': 200
            },
            {
                'name': 'invalid_api_key',
                'headers': {'X-API-Key': 'invalid-key'},
                'expected_status': 401
            },
            {
                'name': 'missing_api_key',
                'headers': {},
                'expected_status': 401
            },
            {
                'name': 'empty_api_key',
                'headers': {'X-API-Key': ''},
                'expected_status': 401
            }
        ]
        
        results = []
        for test in tests:
            response = self._send_request(
                {"text": "Test message"},
                headers=test['headers']
            )
            
            results.append({
                'test_name': test['name'],
                'expected_status': test['expected_status'],
                'actual_status': response.status_code,
                'passed': response.status_code == test['expected_status']
            })
        
        return {
            'status': 'completed',
            'results': results,
            'tests_passed': sum(1 for r in results if r['passed'])
        }
    
    def _test_authorization(self) -> Dict[str, Any]:
        """Test authorization mechanisms."""
        # Test access to different endpoints with different permissions
        endpoints = [
            '/analyze/sync',
            '/analyze/async',
            '/status/test-job-id',
            '/admin/users'
        ]
        
        results = []
        for endpoint in endpoints:
            response = self._send_request(
                {"text": "Test message"},
                endpoint=endpoint
            )
            
            results.append({
                'endpoint': endpoint,
                'status_code': response.status_code,
                'authorized': response.status_code != 403
            })
        
        return {
            'status': 'completed',
            'results': results
        }
    
    def _test_input_validation(self) -> Dict[str, Any]:
        """Test input validation."""
        invalid_inputs = [
            {"text": ""},  # Empty text
            {"text": "x" * 10000},  # Too long
            {"text": None},  # Null value
            {"text": 123},  # Wrong type
            {"invalid_field": "test"},  # Invalid field
            {}  # Empty payload
        ]
        
        results = []
        for invalid_input in invalid_inputs:
            response = self._send_request(invalid_input)
            results.append({
                'input': invalid_input,
                'status_code': response.status_code,
                'properly_validated': response.status_code == 400
            })
        
        return {
            'status': 'completed',
            'results': results,
            'validation_working': all(r['properly_validated'] for r in results)
        }
    
    def _test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting."""
        # Send many requests quickly
        responses = []
        for i in range(20):
            response = self._send_request({"text": f"Test message {i}"})
            responses.append(response.status_code)
        
        rate_limited = any(status == 429 for status in responses)
        
        return {
            'status': 'completed',
            'rate_limiting_working': rate_limited,
            'responses': responses
        }
    
    def _send_request(self, payload: Dict, headers: Dict = None, endpoint: str = '/analyze/sync') -> requests.Response:
        """Send HTTP request."""
        if headers is None:
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key
            }
        
        return requests.post(
            f"{self.base_url}{endpoint}",
            json=payload,
            headers=headers,
            timeout=30
        )
    
    def _is_vulnerable(self, response: requests.Response) -> bool:
        """Check if response indicates vulnerability."""
        # Check for signs of successful injection
        vulnerable_indicators = [
            'error in your SQL syntax',
            'mysql_fetch_array',
            'ORA-01756',
            'Microsoft OLE DB Provider',
            'PostgreSQL query failed'
        ]
        
        response_text = response.text.lower()
        return any(indicator in response_text for indicator in vulnerable_indicators)

# Security test cases
class TestSecurity:
    """Security test cases."""
    
    @pytest.mark.security
    def test_injection_attacks(self):
        """Test for injection vulnerabilities."""
        framework = SecurityTestFramework(
            base_url="https://staging-api.aurastream.com/v1",
            api_key="test-api-key"
        )
        
        results = framework._test_injection_attacks()
        
        assert results['vulnerabilities_found'] == 0, f"Found {results['vulnerabilities_found']} injection vulnerabilities"
    
    @pytest.mark.security
    def test_authentication_security(self):
        """Test authentication security."""
        framework = SecurityTestFramework(
            base_url="https://staging-api.aurastream.com/v1",
            api_key="test-api-key"
        )
        
        results = framework._test_authentication()
        
        assert results['tests_passed'] == len(results['results']), "Some authentication tests failed"
    
    @pytest.mark.security
    def test_input_validation(self):
        """Test input validation security."""
        framework = SecurityTestFramework(
            base_url="https://staging-api.aurastream.com/v1",
            api_key="test-api-key"
        )
        
        results = framework._test_input_validation()
        
        assert results['validation_working'], "Input validation is not working properly"
    
    @pytest.mark.security
    def test_rate_limiting(self):
        """Test rate limiting security."""
        framework = SecurityTestFramework(
            base_url="https://staging-api.aurastream.com/v1",
            api_key="test-api-key"
        )
        
        results = framework._test_rate_limiting()
        
        assert results['rate_limiting_working'], "Rate limiting is not working"
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=src --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Start LocalStack
      run: |
        docker run -d -p 4566:4566 localstack/localstack
    
    - name: Wait for LocalStack
      run: sleep 30
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
      env:
        AWS_ENDPOINT_URL: http://localhost:4566
        AWS_ACCESS_KEY_ID: test
        AWS_SECRET_ACCESS_KEY: test
        AWS_DEFAULT_REGION: us-east-1

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.event_name == 'pull_request'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Deploy to staging
      run: |
        sam build
        sam deploy --config-env staging --no-confirm-changeset
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    
    - name: Run E2E tests
      run: |
        pytest tests/e2e/ -v
      env:
        TEST_BASE_URL: https://staging-api.aurastream.com/v1
        TEST_API_KEY: ${{ secrets.STAGING_API_KEY }}

  performance-tests:
    runs-on: ubuntu-latest
    needs: e2e-tests
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run performance tests
      run: |
        pytest tests/performance/ -v -m performance
      env:
        TEST_BASE_URL: https://staging-api.aurastream.com/v1
        TEST_API_KEY: ${{ secrets.STAGING_API_KEY }}

  security-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run security tests
      run: |
        pytest tests/security/ -v -m security
    
    - name: Run bandit security linter
      run: |
        bandit -r src/ -f json -o bandit-report.json
    
    - name: Upload security report
      uses: actions/upload-artifact@v3
      with:
        name: security-report
        path: bandit-report.json
```

### Test Quality Gates

```python
class QualityGates:
    """Quality gates for CI/CD pipeline."""
    
    GATES = {
        'unit_tests': {
            'coverage_threshold': 80,
            'pass_rate_threshold': 100
        },
        'integration_tests': {
            'pass_rate_threshold': 95
        },
        'e2e_tests': {
            'pass_rate_threshold': 90
        },
        'performance_tests': {
            'response_time_p95': 1000,
            'success_rate': 95
        },
        'security_tests': {
            'vulnerabilities': 0,
            'security_score': 90
        }
    }
    
    @classmethod
    def validate_quality_gate(cls, gate_name: str, results: Dict[str, Any]) -> bool:
        """
        Validate quality gate.
        
        Args:
            gate_name: Name of the quality gate
            results: Test results
            
        Returns:
            True if quality gate passes
        """
        gate_config = cls.GATES.get(gate_name, {})
        
        for metric, threshold in gate_config.items():
            if metric in results:
                if results[metric] < threshold:
                    return False
        
        return True
    
    @classmethod
    def get_quality_report(cls, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate quality report.
        
        Args:
            all_results: Results from all test types
            
        Returns:
            Quality report
        """
        report = {
            'overall_status': 'PASS',
            'gates': {},
            'summary': {}
        }
        
        for gate_name in cls.GATES.keys():
            if gate_name in all_results:
                gate_passed = cls.validate_quality_gate(gate_name, all_results[gate_name])
                report['gates'][gate_name] = {
                    'status': 'PASS' if gate_passed else 'FAIL',
                    'results': all_results[gate_name]
                }
                
                if not gate_passed:
                    report['overall_status'] = 'FAIL'
        
        return report
```

---

## Quality Metrics

### Test Coverage Metrics

```python
class TestCoverageAnalyzer:
    """Analyzes test coverage metrics."""
    
    def __init__(self):
        self.coverage_thresholds = {
            'overall': 80,
            'critical_paths': 95,
            'business_logic': 90,
            'error_handling': 85
        }
    
    def analyze_coverage(self, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze test coverage data.
        
        Args:
            coverage_data: Coverage data from pytest-cov
            
        Returns:
            Coverage analysis results
        """
        analysis = {
            'overall_coverage': coverage_data.get('total_coverage', 0),
            'line_coverage': coverage_data.get('line_coverage', 0),
            'branch_coverage': coverage_data.get('branch_coverage', 0),
            'function_coverage': coverage_data.get('function_coverage', 0),
            'files_covered': len(coverage_data.get('files', [])),
            'files_missing': self._find_uncovered_files(coverage_data),
            'critical_paths_coverage': self._analyze_critical_paths(coverage_data),
            'meets_thresholds': self._check_thresholds(coverage_data)
        }
        
        return analysis
    
    def _find_uncovered_files(self, coverage_data: Dict[str, Any]) -> List[str]:
        """Find files with low coverage."""
        uncovered_files = []
        
        for file_path, file_coverage in coverage_data.get('files', {}).items():
            if file_coverage < 70:  # 70% threshold for individual files
                uncovered_files.append(file_path)
        
        return uncovered_files
    
    def _analyze_critical_paths(self, coverage_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze coverage of critical code paths."""
        critical_paths = {
            'authentication': 0,
            'authorization': 0,
            'data_validation': 0,
            'error_handling': 0,
            'business_logic': 0
        }
        
        # Analyze coverage for each critical path
        # This would need to be customized based on actual code structure
        
        return critical_paths
    
    def _check_thresholds(self, coverage_data: Dict[str, Any]) -> bool:
        """Check if coverage meets all thresholds."""
        for metric, threshold in self.coverage_thresholds.items():
            if metric in coverage_data:
                if coverage_data[metric] < threshold:
                    return False
        
        return True
```

### Test Quality Metrics

```python
class TestQualityMetrics:
    """Tracks and analyzes test quality metrics."""
    
    def __init__(self):
        self.metrics = {
            'test_execution_time': 0,
            'test_pass_rate': 0,
            'test_flakiness': 0,
            'test_maintainability': 0,
            'test_readability': 0
        }
    
    def calculate_metrics(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate test quality metrics.
        
        Args:
            test_results: Test execution results
            
        Returns:
            Quality metrics
        """
        metrics = {
            'execution_time': self._calculate_execution_time(test_results),
            'pass_rate': self._calculate_pass_rate(test_results),
            'flakiness': self._calculate_flakiness(test_results),
            'maintainability': self._calculate_maintainability(test_results),
            'readability': self._calculate_readability(test_results)
        }
        
        return metrics
    
    def _calculate_execution_time(self, test_results: Dict[str, Any]) -> float:
        """Calculate average test execution time."""
        total_time = test_results.get('total_time', 0)
        total_tests = test_results.get('total_tests', 1)
        
        return total_time / total_tests
    
    def _calculate_pass_rate(self, test_results: Dict[str, Any]) -> float:
        """Calculate test pass rate."""
        passed_tests = test_results.get('passed_tests', 0)
        total_tests = test_results.get('total_tests', 1)
        
        return (passed_tests / total_tests) * 100
    
    def _calculate_flakiness(self, test_results: Dict[str, Any]) -> float:
        """Calculate test flakiness rate."""
        flaky_tests = test_results.get('flaky_tests', 0)
        total_tests = test_results.get('total_tests', 1)
        
        return (flaky_tests / total_tests) * 100
    
    def _calculate_maintainability(self, test_results: Dict[str, Any]) -> float:
        """Calculate test maintainability score."""
        # This would analyze test code complexity, duplication, etc.
        # For now, return a placeholder value
        return 85.0
    
    def _calculate_readability(self, test_results: Dict[str, Any]) -> float:
        """Calculate test readability score."""
        # This would analyze test naming, documentation, structure, etc.
        # For now, return a placeholder value
        return 90.0
```

---

This comprehensive testing strategy and quality assurance guide provides the foundation for implementing enterprise-grade testing for the AuraStream platform. It covers all aspects of testing from unit tests to performance testing, ensuring high-quality, reliable, and secure software delivery.
