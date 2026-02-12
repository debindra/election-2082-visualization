"""
Redis Cache Service for Query Results and Embeddings

Provides caching layer for:
- Query results
- Embeddings
- SQL query results
- FAISS search results
"""
import logging
import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List
from pathlib import Path
import numpy as np

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from config.settings import settings

logger = logging.getLogger(__name__)


class RedisCacheService:
    """
    Redis caching service with connection pooling and serialization support.
    
    Cache key patterns:
    - query_result:{query_hash}:{filters_hash} -> JSON response (TTL: 1 hour)
    - embedding:{text_hash} -> numpy array (TTL: 24 hours)
    - sql_query:{query_hash} -> SQL string + results (TTL: 30 minutes)
    - faiss_search:{embedding_hash}:{k}:{filters_hash} -> results (TTL: 15 minutes)
    """
    
    def __init__(self):
        """Initialize Redis cache service."""
        self.enabled = settings.enable_cache and REDIS_AVAILABLE
        
        if not self.enabled:
            if not settings.enable_cache:
                logger.info("Redis caching disabled in settings")
            else:
                logger.warning("Redis not available. Install redis-py: pip install redis")
            self.client = None
            return
        
        try:
            # Create connection pool
            self.pool = redis.ConnectionPool(
                host=getattr(settings, 'redis_host', 'localhost'),
                port=getattr(settings, 'redis_port', 6379),
                db=getattr(settings, 'redis_db', 0),
                password=getattr(settings, 'redis_password', None),
                max_connections=getattr(settings, 'redis_pool_size', 10),
                socket_timeout=getattr(settings, 'redis_socket_timeout', 5),
                socket_connect_timeout=getattr(settings, 'redis_connect_timeout', 5),
                decode_responses=False  # We'll handle encoding/decoding
            )
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            self.client.ping()
            logger.info("Redis cache service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            logger.warning("Caching will be disabled")
            self.enabled = False
            self.client = None
    
    def _generate_hash(self, *args: Any) -> str:
        """
        Generate consistent hash for cache keys.
        
        Args:
            *args: Values to hash
            
        Returns:
            MD5 hex digest
        """
        hash_input = json.dumps(args, sort_keys=True, default=str)
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _serialize_value(self, value: Any) -> bytes:
        """
        Serialize value for Redis storage.
        
        Args:
            value: Value to serialize
            
        Returns:
            Serialized bytes
        """
        if isinstance(value, np.ndarray):
            # Serialize numpy arrays
            return pickle.dumps(value)
        elif isinstance(value, (list, dict)):
            # Serialize JSON-compatible types
            return json.dumps(value).encode('utf-8')
        else:
            # Serialize as string
            return str(value).encode('utf-8')
    
    def _deserialize_value(self, data: bytes, expected_type: type = None) -> Any:
        """
        Deserialize value from Redis.
        
        Args:
            data: Raw bytes from Redis
            expected_type: Expected type for deserialization
            
        Returns:
            Deserialized value
        """
        try:
            # Try pickle first (for numpy arrays)
            try:
                return pickle.loads(data)
            except (pickle.UnpicklingError, AttributeError):
                pass
            
            # Try JSON
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            
            # Return as string
            return data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error deserializing cache value: {e}")
            return None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            data = self.client.get(key)
            if data:
                logger.debug(f"Cache hit for key: {key}")
                return self._deserialize_value(data)
            else:
                logger.debug(f"Cache miss for key: {key}")
                return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            serialized = self._serialize_value(value)
            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
            logger.debug(f"Cached key: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            result = self.client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "query_result:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                count = self.client.delete(*keys)
                logger.info(f"Deleted {count} keys matching pattern: {pattern}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Error deleting pattern: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """
        Clear all cached data.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.flushdb()
            logger.warning("Cleared all cache data")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "enabled": self.enabled,
            "redis_available": REDIS_AVAILABLE,
        }
        
        if not self.enabled or not self.client:
            return stats
        
        try:
            info = self.client.info()
            stats.update({
                "total_keys": self.client.dbsize(),
                "memory_used": info.get("used_memory_human", "N/A"),
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1),
                "connected_clients": info.get("connected_clients", 0),
            })
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
        
        return stats
    
    # ================== Cache Methods ==================
    
    def cache_query_result(self, query: str, filters: Dict[str, Any], result: Any, ttl: int = None) -> bool:
        """
        Cache query result.
        
        Args:
            query: Original query
            filters: Query filters
            result: Query result to cache
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful
        """
        ttl = ttl or getattr(settings, 'cache_query_ttl', 3600)
        key = f"query_result:{self._generate_hash(query, filters)}"
        return self.set(key, result, ttl)
    
    def get_cached_query_result(self, query: str, filters: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached query result.
        
        Args:
            query: Original query
            filters: Query filters
            
        Returns:
            Cached result or None
        """
        key = f"query_result:{self._generate_hash(query, filters)}"
        return self.get(key)
    
    def cache_embedding(self, text: str, embedding: np.ndarray, ttl: int = None) -> bool:
        """
        Cache text embedding.
        
        Args:
            text: Original text
            embedding: Numpy array embedding
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if successful
        """
        ttl = ttl or getattr(settings, 'cache_embedding_ttl', 86400)
        key = f"embedding:{self._generate_hash(text)}"
        return self.set(key, embedding, ttl)
    
    def get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get cached embedding.
        
        Args:
            text: Original text
            
        Returns:
            Cached embedding or None
        """
        key = f"embedding:{self._generate_hash(text)}"
        return self.get(key)
    
    def cache_sql_result(self, query: str, params: tuple, result: Any, ttl: int = None) -> bool:
        """
        Cache SQL query result.
        
        Args:
            query: SQL query
            params: Query parameters
            result: Query result
            ttl: Time to live in seconds (default: 30 minutes)
            
        Returns:
            True if successful
        """
        ttl = ttl or getattr(settings, 'cache_sql_ttl', 1800)
        key = f"sql_query:{self._generate_hash(query, params)}"
        return self.set(key, result, ttl)
    
    def get_cached_sql_result(self, query: str, params: tuple) -> Optional[Any]:
        """
        Get cached SQL result.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Cached result or None
        """
        key = f"sql_query:{self._generate_hash(query, params)}"
        return self.get(key)
    
    def cache_faiss_search(self, embedding_hash: str, k: int, filters: Dict[str, Any], result: Any, ttl: int = None) -> bool:
        """
        Cache FAISS search result.
        
        Args:
            embedding_hash: Hash of query embedding
            k: Number of results
            filters: Search filters
            result: Search result
            ttl: Time to live in seconds (default: 15 minutes)
            
        Returns:
            True if successful
        """
        ttl = ttl or getattr(settings, 'cache_faiss_ttl', 900)
        key = f"faiss_search:{embedding_hash}:{k}:{self._generate_hash(filters)}"
        return self.set(key, result, ttl)
    
    def get_cached_faiss_search(self, embedding_hash: str, k: int, filters: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached FAISS search result.
        
        Args:
            embedding_hash: Hash of query embedding
            k: Number of results
            filters: Search filters
            
        Returns:
            Cached result or None
        """
        key = f"faiss_search:{embedding_hash}:{k}:{self._generate_hash(filters)}"
        return self.get(key)
    
    def invalidate_query_cache(self) -> int:
        """
        Invalidate all query result cache.
        
        Returns:
            Number of keys deleted
        """
        return self.delete_pattern("query_result:*")
    
    def invalidate_sql_cache(self) -> int:
        """
        Invalidate all SQL query cache.
        
        Returns:
            Number of keys deleted
        """
        return self.delete_pattern("sql_query:*")
    
    def invalidate_faiss_cache(self) -> int:
        """
        Invalidate all FAISS search cache.
        
        Returns:
            Number of keys deleted
        """
        return self.delete_pattern("faiss_search:*")
    
    def invalidate_all_cache(self) -> bool:
        """
        Invalidate all cache data.
        
        Returns:
            True if successful
        """
        return self.clear_all()
