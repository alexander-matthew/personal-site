"""Shared test fixtures."""
import os
import shutil
import tempfile
import time

import pytest
from fastapi.testclient import TestClient

from app.services.rate_limit import _rate_limit_store


@pytest.fixture
def app():
    """Create a fresh FastAPI app instance for testing."""
    from app import create_app
    return create_app()


@pytest.fixture
def client(app):
    """Synchronous test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def tmp_cache_dir(tmp_path):
    """Provide a temporary cache directory and clean up after."""
    cache_dir = str(tmp_path / "test_cache")
    os.makedirs(cache_dir, exist_ok=True)
    yield cache_dir
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)


@pytest.fixture(autouse=True)
def clean_rate_limit():
    """Clear rate limit store before each test."""
    _rate_limit_store.clear()
    yield
    _rate_limit_store.clear()
