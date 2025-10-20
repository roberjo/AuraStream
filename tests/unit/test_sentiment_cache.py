"""Tests for sentiment cache."""

import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.cache.sentiment_cache import SentimentCache


class TestSentimentCache:
    """Test sentiment cache functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("src.cache.sentiment_cache.aws_clients") as mock_aws:
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            with patch.dict(os.environ, {"SENTIMENT_CACHE_TABLE": "test-cache-table"}):
                self.cache = SentimentCache()
                self.cache.table = mock_table

    def test_init_default_table(self):
        """Test cache initialization with default table name."""
        with patch("src.cache.sentiment_cache.aws_clients") as mock_aws:
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            with patch.dict(os.environ, {}, clear=True):
                cache = SentimentCache()
                assert cache.table_name == "AuraStream-SentimentCache"

    def test_init_custom_table(self):
        """Test cache initialization with custom table name."""
        with patch("src.cache.sentiment_cache.aws_clients") as mock_aws:
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_dynamodb.Table.return_value = mock_table
            mock_aws.get_dynamodb_resource.return_value = mock_dynamodb

            with patch.dict(os.environ, {"SENTIMENT_CACHE_TABLE": "custom-table"}):
                cache = SentimentCache()
                assert cache.table_name == "custom-table"

    def test_get_cached_result_hit(self):
        """Test getting cached result when item exists and is not expired."""
        mock_item = {
            "text_hash": "test_hash",
            "sentiment_result": {"sentiment": "POSITIVE", "score": 0.95},
            "created_at": datetime.utcnow().isoformat(),
            "ttl": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        }

        self.cache.table.get_item.return_value = {"Item": mock_item}

        result = self.cache.get_cached_result("test text")

        assert result == {"sentiment": "POSITIVE", "score": 0.95}
        self.cache.table.get_item.assert_called_once()

    def test_get_cached_result_miss(self):
        """Test getting cached result when item doesn't exist."""
        self.cache.table.get_item.return_value = {}

        result = self.cache.get_cached_result("test text")

        assert result is None
        self.cache.table.get_item.assert_called_once()

    def test_get_cached_result_expired(self):
        """Test getting cached result when item is expired."""
        mock_item = {
            "text_hash": "test_hash",
            "sentiment_result": {"sentiment": "POSITIVE", "score": 0.95},
            "created_at": datetime.utcnow().isoformat(),
            "ttl": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
        }

        self.cache.table.get_item.return_value = {"Item": mock_item}

        result = self.cache.get_cached_result("test text")

        assert result is None

    def test_get_cached_result_error(self):
        """Test getting cached result with error."""
        self.cache.table.get_item.side_effect = Exception("DynamoDB error")

        result = self.cache.get_cached_result("test text")

        assert result is None

    def test_store_result_success(self):
        """Test storing result successfully."""
        result = {"sentiment": "POSITIVE", "score": 0.95}
        self.cache.table.put_item.return_value = {}

        success = self.cache.store_result("test text", result)

        assert success is True
        self.cache.table.put_item.assert_called_once()

    def test_store_result_with_custom_ttl(self):
        """Test storing result with custom TTL."""
        result = {"sentiment": "POSITIVE", "score": 0.95}
        self.cache.table.put_item.return_value = {}

        success = self.cache.store_result("test text", result, ttl=3600)

        assert success is True
        call_args = self.cache.table.put_item.call_args
        item = call_args[1]["Item"]
        assert "ttl" in item
        assert item["sentiment_result"] == result

    def test_store_result_error(self):
        """Test storing result with error."""
        result = {"sentiment": "POSITIVE", "score": 0.95}
        self.cache.table.put_item.side_effect = Exception("DynamoDB error")

        success = self.cache.store_result("test text", result)

        assert success is False

    def test_delete_result_success(self):
        """Test deleting result successfully."""
        self.cache.table.delete_item.return_value = {}

        success = self.cache.delete_result("test text")

        assert success is True
        self.cache.table.delete_item.assert_called_once()

    def test_delete_result_error(self):
        """Test deleting result with error."""
        self.cache.table.delete_item.side_effect = Exception("DynamoDB error")

        success = self.cache.delete_result("test text")

        assert success is False

    def test_clear_cache_success(self):
        """Test clearing cache successfully."""
        mock_items = [
            {"text_hash": "hash1"},
            {"text_hash": "hash2"},
        ]
        self.cache.table.scan.return_value = {"Items": mock_items}
        self.cache.table.delete_item.return_value = {}

        success = self.cache.clear_cache()

        assert success is True
        self.cache.table.scan.assert_called_once()
        assert self.cache.table.delete_item.call_count == 2

    def test_clear_cache_error(self):
        """Test clearing cache with error."""
        self.cache.table.scan.side_effect = Exception("DynamoDB error")

        success = self.cache.clear_cache()

        assert success is False

    def test_get_cache_stats_success(self):
        """Test getting cache stats successfully."""
        self.cache.table.scan.return_value = {"Count": 42}

        stats = self.cache.get_cache_stats()

        assert stats["total_items"] == 42
        assert stats["table_name"] == "test-cache-table"
        assert "last_updated" in stats

    def test_get_cache_stats_error(self):
        """Test getting cache stats with error."""
        self.cache.table.scan.side_effect = Exception("DynamoDB error")

        stats = self.cache.get_cache_stats()

        assert "error" in stats
        assert stats["table_name"] == "test-cache-table"

    def test_generate_cache_key(self):
        """Test cache key generation."""
        key1 = self.cache._generate_cache_key("Test Text")
        key2 = self.cache._generate_cache_key("test text")
        key3 = self.cache._generate_cache_key("  test text  ")

        # Should be the same for normalized text
        assert key1 == key2 == key3
        assert len(key1) == 64  # SHA256 hex length

    def test_normalize_text(self):
        """Test text normalization."""
        normalized = self.cache._normalize_text("  Test   Text  ")

        assert normalized == "test text"

    def test_is_expired_true(self):
        """Test expired item detection."""
        item = {"ttl": int((datetime.utcnow() - timedelta(hours=1)).timestamp())}

        assert self.cache._is_expired(item) is True

    def test_is_expired_false(self):
        """Test non-expired item detection."""
        item = {"ttl": int((datetime.utcnow() + timedelta(hours=1)).timestamp())}

        assert self.cache._is_expired(item) is False

    def test_is_expired_no_ttl(self):
        """Test expired item detection with no TTL."""
        item = {}

        assert self.cache._is_expired(item) is True

    def test_is_expired_invalid_ttl(self):
        """Test expired item detection with invalid TTL."""
        item = {"ttl": "invalid"}

        assert self.cache._is_expired(item) is True
