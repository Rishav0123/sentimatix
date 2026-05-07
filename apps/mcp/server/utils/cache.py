import time
import functools
import logging
import asyncio
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class TTLCache:
    """Simple in-memory cache with Time-To-Live (TTL) expiration."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default expiration time in seconds (default: 300s = 5m)
        """
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._default_ttl = default_ttl
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        if key in self._cache:
            expiry, value = self._cache[key]
            if time.time() < expiry:
                return value
            else:
                del self._cache[key]  # Remove expired
        return None
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        expiry = time.time() + (ttl if ttl is not None else self._default_ttl)
        self._cache[key] = (expiry, value)
        
    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()

# Global cache instance
analysis_cache = TTLCache(default_ttl=300) # 5 minutes

def cache_result(ttl_seconds: int = 300):
    """
    Decorator to cache function results.
    Key is generated from function name and arguments.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from arguments
            # Note: args[0] is 'self' for methods, we might want to include it or not
            # For simplicity, we use string representation of all args
            key_parts = [func.__name__]
            key_parts.extend([str(a) for a in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            key = ":".join(key_parts)
            
            # Check cache
            cached = analysis_cache.get(key)
            if cached is not None:
                logger.debug(f"Cache hit for {key}")
                return cached
                
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result (only if successful? assuming result is valid)
            analysis_cache.set(key, result, ttl=ttl_seconds)
            return result
            
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Async version
            key_parts = [func.__name__]
            key_parts.extend([str(a) for a in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            key = ":".join(key_parts)
            
            cached = analysis_cache.get(key)
            if cached is not None:
                logger.debug(f"Cache hit for {key}")
                return cached
                
            result = await func(*args, **kwargs)
            analysis_cache.set(key, result, ttl=ttl_seconds)
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator
