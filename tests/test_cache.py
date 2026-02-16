"""Tests for app/services/cache.py."""
import json
import os
import time

from app.services.cache import SimpleCache, cached


class TestSimpleCache:
    """Tests for SimpleCache get/set."""

    def test_get_returns_none_for_missing_key(self, tmp_cache_dir):
        c = SimpleCache(cache_dir=tmp_cache_dir)
        assert c.get("nonexistent") is None

    def test_set_and_get_round_trip(self, tmp_cache_dir):
        c = SimpleCache(cache_dir=tmp_cache_dir)
        c.set("key1", {"data": 42}, ttl_seconds=60)
        assert c.get("key1") == {"data": 42}

    def test_set_overwrites_previous_value(self, tmp_cache_dir):
        c = SimpleCache(cache_dir=tmp_cache_dir)
        c.set("key1", "first", ttl_seconds=60)
        c.set("key1", "second", ttl_seconds=60)
        assert c.get("key1") == "second"

    def test_expired_entry_returns_none(self, tmp_cache_dir):
        c = SimpleCache(cache_dir=tmp_cache_dir)
        c.set("key1", "value", ttl_seconds=0)
        # TTL=0 means it expires immediately (datetime.now() + 0 seconds)
        time.sleep(0.01)
        assert c.get("key1") is None

    def test_expired_entry_is_deleted(self, tmp_cache_dir):
        c = SimpleCache(cache_dir=tmp_cache_dir)
        c.set("key1", "value", ttl_seconds=0)
        time.sleep(0.01)
        c.get("key1")  # triggers deletion
        cache_files = os.listdir(tmp_cache_dir)
        assert len(cache_files) == 0

    def test_corrupted_cache_file_returns_none(self, tmp_cache_dir):
        c = SimpleCache(cache_dir=tmp_cache_dir)
        # Write garbage to a cache file
        c.set("key1", "value", ttl_seconds=60)
        path = c._get_cache_path("key1")
        with open(path, 'w') as f:
            f.write("not valid json{{{")
        assert c.get("key1") is None

    def test_cache_stores_various_types(self, tmp_cache_dir):
        c = SimpleCache(cache_dir=tmp_cache_dir)
        c.set("str", "hello", ttl_seconds=60)
        c.set("int", 42, ttl_seconds=60)
        c.set("list", [1, 2, 3], ttl_seconds=60)
        c.set("dict", {"nested": {"deep": True}}, ttl_seconds=60)
        assert c.get("str") == "hello"
        assert c.get("int") == 42
        assert c.get("list") == [1, 2, 3]
        assert c.get("dict") == {"nested": {"deep": True}}

    def test_creates_cache_dir_if_missing(self, tmp_path):
        cache_dir = str(tmp_path / "new_cache_dir")
        assert not os.path.exists(cache_dir)
        c = SimpleCache(cache_dir=cache_dir)
        assert os.path.exists(cache_dir)


class TestCachedDecorator:
    """Tests for the @cached decorator."""

    def test_caches_function_result(self, tmp_cache_dir):
        call_count = 0
        c = SimpleCache(cache_dir=tmp_cache_dir)

        # Monkey-patch the global cache for this test
        import app.services.cache as cache_module
        original = cache_module.cache
        cache_module.cache = c
        try:
            @cached(ttl_seconds=60, key_prefix='test')
            def expensive():
                nonlocal call_count
                call_count += 1
                return {"result": call_count}

            first = expensive()
            second = expensive()
            assert first == second
            assert call_count == 1  # only called once
        finally:
            cache_module.cache = original

    def test_different_args_produce_different_keys(self, tmp_cache_dir):
        c = SimpleCache(cache_dir=tmp_cache_dir)

        import app.services.cache as cache_module
        original = cache_module.cache
        cache_module.cache = c
        try:
            @cached(ttl_seconds=60, key_prefix='test')
            def add(a, b):
                return a + b

            assert add(1, 2) == 3
            assert add(3, 4) == 7
        finally:
            cache_module.cache = original
