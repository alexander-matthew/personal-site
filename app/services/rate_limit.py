"""
Simple in-memory rate limiting as FastAPI dependency.
For production, consider Redis-based rate limiting.
"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException

# In-memory store (resets on app restart)
_rate_limit_store = defaultdict(list)


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
        window_start = now - window_seconds

        # Clean old entries
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
