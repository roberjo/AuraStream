"""Unit tests for cache module."""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

from src.cache.sentiment_cache import SentimentCache


class TestSentimentCache:
    """Test SentimentCache class."""
    
    @pytest.fixture
    def cache(self):
        """Create a SentimentCache instance for testing."""
        return SentimentCache()
    
    @pytest.fixture
    def sample_result(self):
        """Sample cached result."""
        return {
            'sentiment': 'POSITIVE',
            'score': 0.95,
            'language_code': 'en',
            'confidence': True,
            'pii_detected': False,
            'processing_time_ms': 150
        }
    
    def test_cache_initialization(self, cache):
        """Test cache initialization."""
        assert cache.table_name == 'aurastream-sentiment-cache'
        assert cache.ttl_seconds == 3600  # 1 hour default
    
    @patch('src.cache.sentiment_cache.aws_clients')
    def test_get_cached_result_hit(self, mock_aws_clients, cache, sample_result):
        """Test getting cached result when hit."""
        # Mock DynamoDB response
        mock_dynamodb = Mock()
        mock_aws_clients.dynamodb = mock_dynamodb
        
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock successful get_item response
        mock_table.get_item.return_value = {
            'Item': {
                'text_hash': 'test-hash',
                'result': json.dumps(sample_result),
                'ttl': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            }
        }
        
        result = cache.get_cached_result("test text")
        
        assert result == sample_result
        mock_table.get_item.assert_called_once()
    
    @patch('src.cache.sentiment_cache.aws_clients')
    def test_get_cached_result_miss(self, mock_aws_clients, cache):
        """Test getting cached result when miss."""
        # Mock DynamoDB response
        mock_dynamodb = Mock()
        mock_aws_clients.dynamodb = mock_dynamodb
        
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock empty get_item response
        mock_table.get_item.return_value = {}
        
        result = cache.get_cached_result("test text")
        
        assert result is None
        mock_table.get_item.assert_called_once()
    
    @patch('src.cache.sentiment_cache.aws_clients')
    def test_get_cached_result_expired(self, mock_aws_clients, cache, sample_result):
        """Test getting cached result when expired."""
        # Mock DynamoDB response
        mock_dynamodb = Mock()
        mock_aws_clients.dynamodb = mock_dynamodb
        
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock expired item
        expired_ttl = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        mock_table.get_item.return_value = {
            'Item': {
                'text_hash': 'test-hash',
                'result': json.dumps(sample_result),
                'ttl': expired_ttl
            }
        }
        
        result = cache.get_cached_result("test text")
        
        assert result is None
    
    @patch('src.cache.sentiment_cache.aws_clients')
    def test_store_result_success(self, mock_aws_clients, cache, sample_result):
        """Test storing result successfully."""
        # Mock DynamoDB response
        mock_dynamodb = Mock()
        mock_aws_clients.dynamodb = mock_dynamodb
        
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock successful put_item response
        mock_table.put_item.return_value = {}
        
        result = cache.store_result("test text", sample_result)
        
        assert result is True
        mock_table.put_item.assert_called_once()
        
        # Verify the put_item call arguments
        call_args = mock_table.put_item.call_args[1]
        assert 'Item' in call_args
        assert 'text_hash' in call_args['Item']
        assert 'result' in call_args['Item']
        assert 'ttl' in call_args['Item']
    
    @patch('src.cache.sentiment_cache.aws_clients')
    def test_store_result_failure(self, mock_aws_clients, cache, sample_result):
        """Test storing result failure."""
        # Mock DynamoDB response
        mock_dynamodb = Mock()
        mock_aws_clients.dynamodb = mock_dynamodb
        
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock put_item failure
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        
        result = cache.store_result("test text", sample_result)
        
        assert result is False
    
    @patch('src.cache.sentiment_cache.aws_clients')
    def test_clear_cache_success(self, mock_aws_clients, cache):
        """Test clearing cache successfully."""
        # Mock DynamoDB response
        mock_dynamodb = Mock()
        mock_aws_clients.dynamodb = mock_dynamodb
        
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock successful scan and batch_writer
        mock_table.scan.return_value = {
            'Items': [
                {'text_hash': 'hash1'},
                {'text_hash': 'hash2'}
            ]
        }
        
        mock_batch_writer = Mock()
        mock_table.batch_writer.return_value.__enter__.return_value = mock_batch_writer
        
        result = cache.clear_cache()
        
        assert result is True
        mock_table.scan.assert_called_once()
        assert mock_batch_writer.delete_item.call_count == 2
    
    @patch('src.cache.sentiment_cache.aws_clients')
    def test_clear_cache_failure(self, mock_aws_clients, cache):
        """Test clearing cache failure."""
        # Mock DynamoDB response
        mock_dynamodb = Mock()
        mock_aws_clients.dynamodb = mock_dynamodb
        
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock scan failure
        mock_table.scan.side_effect = Exception("DynamoDB error")
        
        result = cache.clear_cache()
        
        assert result is False
    
    def test_generate_text_hash(self, cache):
        """Test text hash generation."""
        text1 = "I love this product!"
        text2 = "I love this product!"
        text3 = "I hate this product!"
        
        hash1 = cache._generate_text_hash(text1)
        hash2 = cache._generate_text_hash(text2)
        hash3 = cache._generate_text_hash(text3)
        
        # Same text should generate same hash
        assert hash1 == hash2
        
        # Different text should generate different hash
        assert hash1 != hash3
        
        # Hash should be a string
        assert isinstance(hash1, str)
        assert len(hash1) > 0
    
    def test_calculate_ttl(self, cache):
        """Test TTL calculation."""
        ttl = cache._calculate_ttl()
        
        # TTL should be in the future
        current_time = datetime.now(timezone.utc).timestamp()
        assert ttl > current_time
        
        # TTL should be approximately 1 hour from now
        expected_ttl = current_time + 3600
        assert abs(ttl - expected_ttl) < 10  # Allow 10 seconds tolerance
    
    def test_custom_ttl(self):
        """Test cache with custom TTL."""
        cache = SentimentCache(ttl_seconds=7200)  # 2 hours
        
        assert cache.ttl_seconds == 7200
        
        ttl = cache._calculate_ttl()
        current_time = datetime.now(timezone.utc).timestamp()
        expected_ttl = current_time + 7200
        assert abs(ttl - expected_ttl) < 10
