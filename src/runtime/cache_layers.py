"""Multi-layer caching system with Redis support."""

import json
import time
from typing import Any, Optional, Dict, List
from abc import ABC, abstractmethod
from src.runtime.cache import DiskCache


class CacheLayer(ABC):
    """Abstract base class for cache layers."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class MemoryCache(CacheLayer):
    """In-memory cache layer."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        if key not in self._cache:
            return None
        
        item = self._cache[key]
        if item['expires_at'] and time.time() > item['expires_at']:
            del self._cache[key]
            return None
        
        return item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache."""
        if len(self._cache) >= self.max_size:
            # Remove oldest item
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].get('created_at', 0))
            del self._cache[oldest_key]
        
        expires_at = time.time() + ttl if ttl else None
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        return True
    
    def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        return key in self._cache and (
            not self._cache[key]['expires_at'] or 
            time.time() <= self._cache[key]['expires_at']
        )


class RedisCache(CacheLayer):
    """Redis cache layer."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis."""
        try:
            import redis
            self._redis = redis.from_url(self.redis_url)
            # Test connection
            self._redis.ping()
        except ImportError:
            print("WARNING: redis package not installed. Redis caching disabled.")
            self._redis = None
        except Exception as e:
            print(f"WARNING: Redis connection failed: {e}. Redis caching disabled.")
            self._redis = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self._redis:
            return None
        
        try:
            value = self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        if not self._redis:
            return False
        
        try:
            serialized = json.dumps(value)
            if ttl:
                return self._redis.setex(key, ttl, serialized)
            else:
                return self._redis.set(key, serialized)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from Redis cache."""
        if not self._redis:
            return False
        
        try:
            return bool(self._redis.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        if not self._redis:
            return False
        
        try:
            return bool(self._redis.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False


class MultiLayerCache:
    """Multi-layer cache with fallback strategy."""
    
    def __init__(self, layers: List[CacheLayer]):
        self.layers = layers
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache layers (L1 -> L2 -> L3)."""
        for i, layer in enumerate(self.layers):
            value = layer.get(key)
            if value is not None:
                # Populate higher layers for faster access next time
                for j in range(i):
                    self.layers[j].set(key, value)
                return value
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in all cache layers."""
        success = True
        for layer in self.layers:
            if not layer.set(key, value, ttl):
                success = False
        return success
    
    def delete(self, key: str) -> bool:
        """Delete value from all cache layers."""
        success = True
        for layer in self.layers:
            if not layer.delete(key):
                success = False
        return success
    
    def exists(self, key: str) -> bool:
        """Check if key exists in any cache layer."""
        for layer in self.layers:
            if layer.exists(key):
                return True
        return False


def create_cache_stack(disk_cache: DiskCache, 
                      memory_size: int = 1000,
                      redis_url: Optional[str] = None) -> MultiLayerCache:
    """Create a multi-layer cache stack."""
    layers = []
    
    # L1: Memory cache (fastest)
    layers.append(MemoryCache(max_size=memory_size))
    
    # L2: Disk cache (persistent)
    layers.append(disk_cache)
    
    # L3: Redis cache (distributed, optional)
    if redis_url:
        layers.append(RedisCache(redis_url=redis_url))
    
    return MultiLayerCache(layers)


class CacheStats:
    """Cache statistics and monitoring."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
    
    def hit(self):
        """Record a cache hit."""
        self.hits += 1
    
    def miss(self):
        """Record a cache miss."""
        self.misses += 1
    
    def set(self):
        """Record a cache set."""
        self.sets += 1
    
    def delete(self):
        """Record a cache delete."""
        self.deletes += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2)
        }
