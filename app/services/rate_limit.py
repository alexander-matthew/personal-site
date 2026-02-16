"""
Simple in-memory rate limiting as FastAPI dependency.
For production, consider Redis-based rate limiting.
"""
import logging
import time
from collections import defaultdict
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

# In-memory store (resets on app restart)
_rate_limit_store: dict[str, list[float]] = defaultdict(list)

# Maximum number of unique keys to track (prevents unbounded memory growth)
_MAX_KEYS = 10_000

# Timestamp of last full cleanup
_last_cleanup = 0.0


def _cleanup_store(now: float, max_window: int = 300):
    """Remove all entries older than max_window seconds. Runs at most once per minute."""
    global _last_cleanup
    if now - _last_cleanup < 60:
        return
    _last_cleanup = now
    cutoff = now - max_window
    stale_keys = [k for k, v in _rate_limit_store.items() if not v or v[-1] < cutoff]
    for k in stale_keys:
        del _rate_limit_store[k]


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """
    Create a FastAPI dependency for rate limiting.

    Usage:
        @router.get("/api/data", dependencies=[Depends(rate_limit(30, 60))])
        async def get_data(): ...
    """
    async def dependency(request: Request):
        client_id = request.client.host if request.client else 'unknown'
        key = f"{request.url.path}:{client_id}"

        now = time.time()

        # Periodic cleanup to bound memory usage
        _cleanup_store(now)

        # Evict oldest keys if store grows too large
        if len(_rate_limit_store) > _MAX_KEYS and key not in _rate_limit_store:
            oldest_key = min(_rate_limit_store, key=lambda k: _rate_limit_store[k][-1] if _rate_limit_store[k] else 0)
            del _rate_limit_store[oldest_key]

        window_start = now - window_seconds

        # Clean old entries for this key
        _rate_limit_store[key] = [
            t for t in _rate_limit_store[key] if t > window_start
        ]

        # Check limit
        if len(_rate_limit_store[key]) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail={'error': 'Rate limit exceeded', 'retry_after': window_seconds}
            )

        # Record request
        _rate_limit_store[key].append(now)

    return dependency
