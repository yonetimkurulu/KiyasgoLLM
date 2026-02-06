"""
Redis Cache Layer
API response ve engine sonuçları için cache.
"""
import json
import hashlib
from typing import Optional, Any
from functools import wraps
import structlog

from src.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class RedisCache:
    """
    Redis-based caching for API responses.
    
    TTL defaults:
    - products: 24 hours
    - signals: 2 hours
    - comparisons: 6 hours
    - recommendations: 12 hours
    """
    
    TTL_PRODUCTS = 86400      # 24 hours
    TTL_SIGNALS = 7200        # 2 hours
    TTL_COMPARISONS = 21600   # 6 hours
    TTL_RECOMMENDATIONS = 43200  # 12 hours
    
    def __init__(self):
        self._client = None
        self.enabled = settings.cache_enabled
        self.prefix = "kiyasgo:"
    
    @property
    def client(self):
        """Lazy-load Redis client."""
        if self._client is None and self.enabled:
            self._client = self._connect()
        return self._client
    
    def _connect(self):
        """Connect to Redis."""
        try:
            import redis
            return redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        except ImportError:
            logger.warning("Redis not installed, cache disabled")
            self.enabled = False
            return None
        except Exception as e:
            logger.error("Redis connection failed", error=str(e))
            self.enabled = False
            return None
    
    def _make_key(self, namespace: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"{self.prefix}{namespace}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled or not self.client:
            return None
        
        try:
            data = self.client.get(key)
            if data:
                logger.debug("Cache hit", key=key)
                return json.loads(data)
            logger.debug("Cache miss", key=key)
            return None
        except Exception as e:
            logger.error("Cache get error", error=str(e))
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        if not self.enabled or not self.client:
            return False
        
        try:
            data = json.dumps(value, default=str)
            self.client.setex(key, ttl, data)
            logger.debug("Cache set", key=key, ttl=ttl)
            return True
        except Exception as e:
            logger.error("Cache set error", error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error("Cache delete error", error=str(e))
            return False
    
    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        if not self.enabled or not self.client:
            return 0
        
        try:
            pattern = f"{self.prefix}{namespace}:*"
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.error("Cache clear error", error=str(e))
            return 0


# Decorator for caching function results
def cached(namespace: str, ttl: int = 3600):
    """Decorator to cache async function results."""
    cache = RedisCache()
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache._make_key(namespace, *args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl)
            return result
        
        return wrapper
    return decorator
