"""
Caching utilities.
"""

from functools import lru_cache
from typing import Any, Callable, Optional
import json

# Simple in-memory cache
_cache: dict = {}


def get_cache(key: str) -> Optional[Any]:
    """Get a value from the cache."""
    return _cache.get(key)


def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Set a value in the cache."""
    # Note: TTL not implemented in simple cache
    _cache[key] = value


def clear_cache(key: Optional[str] = None) -> None:
    """Clear the cache."""
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()


def cached(key_prefix: str = ""):
    """Decorator for caching function results."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"

            result = get_cache(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            set_cache(cache_key, result)
            return result

        return wrapper

    return decorator
