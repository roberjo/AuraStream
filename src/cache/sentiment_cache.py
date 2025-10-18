"""Sentiment analysis result caching service."""

import hashlib
import json
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.utils.aws_clients import aws_clients
from src.utils.constants import CACHE_TTL_DEFAULT

logger = logging.getLogger(__name__)


class SentimentCache:
    """Manages caching of sentiment analysis results."""
    
    def __init__(self):
        """Initialize sentiment cache."""
        self.table_name = os.environ.get('SENTIMENT_CACHE_TABLE', 'AuraStream-SentimentCache')
        self.dynamodb = aws_clients.get_dynamodb_resource()
        self.table = self.dynamodb.Table(self.table_name)
    
    def get_cached_result(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Get cached sentiment analysis result.
        
        Args:
            text: Text to look up in cache
            
        Returns:
            Cached result if found, None otherwise
        """
        try:
            cache_key = self._generate_cache_key(text)
            
            response = self.table.get_item(
                Key={'text_hash': cache_key}
            )
            
            if 'Item' in response:
                item = response['Item']
                
                # Check if item has expired
                if self._is_expired(item):
                    logger.info(f"Cache item expired for key: {cache_key}")
                    return None
                
                logger.info(f"Cache hit for key: {cache_key}")
                return item.get('sentiment_result')
            
            logger.info(f"Cache miss for key: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached result: {str(e)}")
            return None
    
    def store_result(self, text: str, result: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store sentiment analysis result in cache.
        
        Args:
            text: Original text
            result: Analysis result to cache
            ttl: Time to live in seconds
            
        Returns:
            True if stored successfully
        """
        try:
            cache_key = self._generate_cache_key(text)
            ttl_seconds = ttl or CACHE_TTL_DEFAULT
            
            item = {
                'text_hash': cache_key,
                'sentiment_result': result,
                'created_at': datetime.utcnow().isoformat(),
                'ttl': int((datetime.utcnow() + timedelta(seconds=ttl_seconds)).timestamp())
            }
            
            self.table.put_item(Item=item)
            logger.info(f"Stored result in cache with key: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing result in cache: {str(e)}")
            return False
    
    def delete_result(self, text: str) -> bool:
        """
        Delete cached result.
        
        Args:
            text: Text to delete from cache
            
        Returns:
            True if deleted successfully
        """
        try:
            cache_key = self._generate_cache_key(text)
            
            self.table.delete_item(
                Key={'text_hash': cache_key}
            )
            
            logger.info(f"Deleted cache item with key: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting cache item: {str(e)}")
            return False
    
    def clear_cache(self) -> bool:
        """
        Clear all cached results.
        
        Returns:
            True if cleared successfully
        """
        try:
            # Scan and delete all items
            response = self.table.scan()
            
            for item in response['Items']:
                self.table.delete_item(
                    Key={'text_hash': item['text_hash']}
                )
            
            logger.info("Cleared all cache items")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        try:
            response = self.table.scan(Select='COUNT')
            
            return {
                'total_items': response['Count'],
                'table_name': self.table_name,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {
                'error': str(e),
                'table_name': self.table_name
            }
    
    def _generate_cache_key(self, text: str) -> str:
        """
        Generate cache key for text.
        
        Args:
            text: Text to generate key for
            
        Returns:
            Cache key
        """
        # Normalize text for consistent hashing
        normalized_text = self._normalize_text(text)
        
        # Generate SHA256 hash
        return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent caching.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Convert to lowercase and strip whitespace
        normalized = text.lower().strip()
        
        # Remove extra whitespace
        import re
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """
        Check if cache item has expired.
        
        Args:
            item: Cache item
            
        Returns:
            True if expired
        """
        ttl = item.get('ttl')
        if not ttl:
            return True
        
        current_time = datetime.utcnow().timestamp()
        return current_time > ttl
