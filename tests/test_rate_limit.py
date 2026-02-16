"""Tests for app/services/rate_limit.py."""
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.services.rate_limit import rate_limit, _rate_limit_store


def _make_app(max_requests=3, window_seconds=60):
    """Create a minimal app with a rate-limited endpoint."""
    app = FastAPI()

    @app.get("/test", dependencies=[Depends(rate_limit(max_requests, window_seconds))])
    async def test_endpoint():
        return {"ok": True}

    @app.get("/other", dependencies=[Depends(rate_limit(max_requests, window_seconds))])
    async def other_endpoint():
        return {"ok": True}

    return app


class TestRateLimit:

    def test_allows_requests_under_limit(self):
        app = _make_app(max_requests=5)
        client = TestClient(app)
        for _ in range(5):
            resp = client.get("/test")
            assert resp.status_code == 200

    def test_blocks_requests_over_limit(self):
        app = _make_app(max_requests=3)
        client = TestClient(app)
        for _ in range(3):
            client.get("/test")
        resp = client.get("/test")
        assert resp.status_code == 429

    def test_returns_retry_after_in_body(self):
        app = _make_app(max_requests=1, window_seconds=30)
        client = TestClient(app)
        client.get("/test")
        resp = client.get("/test")
        assert resp.status_code == 429
        body = resp.json()
        assert body["detail"]["retry_after"] == 30

    def test_different_paths_have_separate_limits(self):
        app = _make_app(max_requests=2)
        client = TestClient(app)
        # Fill up /test
        client.get("/test")
        client.get("/test")
        assert client.get("/test").status_code == 429
        # /other should still work
        assert client.get("/other").status_code == 200

    def test_sliding_window_cleans_old_entries(self):
        """Entries older than the window should be cleaned up."""
        import time
        app = _make_app(max_requests=2, window_seconds=1)
        client = TestClient(app)
        client.get("/test")
        client.get("/test")
        assert client.get("/test").status_code == 429
        time.sleep(1.1)
        assert client.get("/test").status_code == 200

    def test_rate_limit_store_cleared_by_fixture(self):
        """Verify the clean_rate_limit fixture works (store should be empty)."""
        assert len(_rate_limit_store) == 0
