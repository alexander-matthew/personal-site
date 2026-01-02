"""
Simple in-memory rate limiting.
For production, consider Redis-based rate limiting.
"""
import time
from functools import wraps
from flask import request, jsonify
from collections import defaultdict

# In-memory store (resets on app restart)
_rate_limit_store = defaultdict(list)


def rate_limit(max_requests=60, window_seconds=60):
    """
    Decorator to rate limit routes.

    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use IP address as identifier
            client_id = request.remote_addr
            key = f"{f.__name__}:{client_id}"

            now = time.time()
            window_start = now - window_seconds

            # Clean old entries
            _rate_limit_store[key] = [
                t for t in _rate_limit_store[key] if t > window_start
            ]

            # Check limit
            if len(_rate_limit_store[key]) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window_seconds
                }), 429

            # Record request
            _rate_limit_store[key].append(now)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
