"""Unit tests for sync handler."""

import json
import pytest
from unittest.mock import Mock, patch
from src.handlers.sync_handler import lambda_handler
from src.models.request_models import SentimentAnalysisRequest


class TestSyncHandler:
    """Test suite for sync handler."""
    
    def test_successful_sentiment_analysis(self, api_event, lambda_context, mock_comprehend_response):
        """Test successful sentiment analysis."""
        with patch('src.handlers.sync_handler._analyze_sentiment') as mock_analyze:
            mock_analyze.return_value = mock_comprehend_response
            
            with patch('src.handlers.sync_handler.SentimentCache') as mock_cache:
                mock_cache.return_value.get_cached_result.return_value = None
                mock_cache.return_value.store_result.return_value = True
                
                with patch('src.handlers.sync_handler.PIIDetector') as mock_pii:
                    mock_pii.return_value.detect_pii.return_value = {'pii_detected': False}
                    
                    response = lambda_handler(api_event, lambda_context)
                    
                    assert response['statusCode'] == 200
                    body = json.loads(response['body'])
                    assert body['sentiment'] == 'POSITIVE'
                    assert body['score'] == 0.95
                    assert body['language_code'] == 'en'
    
    def test_invalid_text_validation(self, lambda_context):
        """Test validation of invalid text input."""
        event = {
            'httpMethod': 'POST',
            'path': '/analyze/sync',
            'body': '{"text": ""}',
            'headers': {'Content-Type': 'application/json'}
        }
        
        response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'VALIDATION_ERROR'
    
    def test_text_length_validation(self, lambda_context):
        """Test validation of text length limits."""
        long_text = "x" * 5001  # Exceeds 5000 character limit
        event = {
            'httpMethod': 'POST',
            'path': '/analyze/sync',
            'body': f'{{"text": "{long_text}"}}',
            'headers': {'Content-Type': 'application/json'}
        }
        
        response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'VALIDATION_ERROR'
    
    def test_cache_hit_scenario(self, api_event, lambda_context, mock_comprehend_response):
        """Test cache hit scenario."""
        cached_result = {
            'sentiment': 'POSITIVE',
            'score': 0.95,
            'language_code': 'en',
            'confidence': 0.98
        }
        
        with patch('src.handlers.sync_handler.SentimentCache') as mock_cache:
            mock_cache.return_value.get_cached_result.return_value = cached_result
            
            response = lambda_handler(api_event, lambda_context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['sentiment'] == 'POSITIVE'
            assert body['cache_hit'] is True
    
    def test_pii_detection(self, api_event, lambda_context, mock_comprehend_response):
        """Test PII detection functionality."""
        # Modify the event to include PII detection option
        pii_event = api_event.copy()
        pii_event['body'] = '{"text": "I love this product!", "options": {"include_pii_detection": true}}'
        
        with patch('src.handlers.sync_handler._analyze_sentiment') as mock_analyze:
            mock_analyze.return_value = mock_comprehend_response
            
            with patch('src.handlers.sync_handler.SentimentCache') as mock_cache:
                mock_cache.return_value.get_cached_result.return_value = None
                mock_cache.return_value.store_result.return_value = True
                
                with patch('src.handlers.sync_handler.PIIDetector') as mock_pii:
                    mock_pii.return_value.detect_pii.return_value = {'pii_detected': True}
                    
                    response = lambda_handler(pii_event, lambda_context)
                    
                    assert response['statusCode'] == 200
                    body = json.loads(response['body'])
                    assert body['pii_detected'] is True
    
    def test_security_validation(self, lambda_context):
        """Test security validation for malicious input."""
        malicious_text = "'; DROP TABLE users; --"
        event = {
            'httpMethod': 'POST',
            'path': '/analyze/sync',
            'body': f'{{"text": "{malicious_text}"}}',
            'headers': {'Content-Type': 'application/json'}
        }
        
        response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'VALIDATION_ERROR'
        assert 'malicious content' in body['error']['message']
    
    def test_error_handling(self, api_event, lambda_context):
        """Test error handling for internal errors."""
        with patch('src.handlers.sync_handler._analyze_sentiment') as mock_analyze:
            mock_analyze.side_effect = Exception("Test error")
            
            response = lambda_handler(api_event, lambda_context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['error']['code'] == 'INTERNAL_ERROR'
    
    @pytest.mark.parametrize("sentiment,expected_score", [
        ("POSITIVE", 0.95),
        ("NEGATIVE", 0.02),
        ("NEUTRAL", 0.02),
        ("MIXED", 0.01)
    ])
    def test_sentiment_score_extraction(self, sentiment, expected_score):
        """Test sentiment score extraction from Comprehend response."""
        from src.handlers.sync_handler import _get_sentiment_score
        
        comprehend_response = {
            'Sentiment': sentiment,
            'SentimentScore': {
                'Positive': 0.95,
                'Negative': 0.02,
                'Neutral': 0.02,
                'Mixed': 0.01
            }
        }
        
        score = _get_sentiment_score(comprehend_response)
        assert score == expected_score
