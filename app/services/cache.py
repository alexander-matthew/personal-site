"""
Simple file-based caching for API responses.
For production with persistence, consider Redis.
"""
import os
import json
import hashlib
from datetime import datetime, timedelta
from functools import wraps


class SimpleCache:
    """File-based cache with TTL support."""

    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or '/tmp/app_cache'
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key):
        """Generate cache file path from key."""
        hashed = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed}.json")

    def get(self, key):
        """Get cached value if not expired."""
        path = self._get_cache_path(key)
        if not os.path.exists(path):
            return None

        try:
            with open(path, 'r') as f:
                data = json.load(f)

            expires_at = datetime.fromisoformat(data['expires_at'])
            if datetime.now() > expires_at:
                os.remove(path)
                return None

            return data['value']
        except (json.JSONDecodeError, KeyError):
            return None

    def set(self, key, value, ttl_seconds=3600):
        """Cache value with TTL."""
        path = self._get_cache_path(key)
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        with open(path, 'w') as f:
            json.dump({
                'value': value,
                'expires_at': expires_at.isoformat()
            }, f)


# Global cache instance
cache = SimpleCache()


def cached(ttl_seconds=3600, key_prefix=''):
    """Decorator to cache function results."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"{key_prefix}:{f.__name__}:{str(args)}:{str(kwargs)}"

            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = f(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result
        return decorated_function
    return decorator
