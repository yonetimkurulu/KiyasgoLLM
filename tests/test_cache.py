"""
Tests for Redis Cache module.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.cache.redis_cache import RedisCache, cached


class TestRedisCacheDisabled:
    """Tests for cache when disabled or Redis unavailable."""

    def test_cache_disabled_returns_none(self):
        cache = RedisCache()
        cache.enabled = False

    @pytest.mark.asyncio
    async def test_get_when_disabled(self):
        cache = RedisCache()
        cache.enabled = False
        result = await cache.get("some_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_when_disabled(self):
        cache = RedisCache()
        cache.enabled = False
        result = await cache.set("key", {"data": 1})
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_when_disabled(self):
        cache = RedisCache()
        cache.enabled = False
        result = await cache.delete("key")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_namespace_when_disabled(self):
        cache = RedisCache()
        cache.enabled = False
        result = await cache.clear_namespace("products")
        assert result == 0


class TestRedisCacheWithMock:
    """Tests for cache with mocked Redis client."""

    def _make_cache_with_mock(self):
        cache = RedisCache()
        cache.enabled = True
        mock_client = MagicMock()
        cache._client = mock_client
        return cache, mock_client

    @pytest.mark.asyncio
    async def test_get_cache_hit(self):
        cache, mock_client = self._make_cache_with_mock()
        mock_client.get.return_value = json.dumps({"name": "Samsung"})

        result = await cache.get("kiyasgo:products:abc123")
        assert result == {"name": "Samsung"}
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_miss(self):
        cache, mock_client = self._make_cache_with_mock()
        mock_client.get.return_value = None

        result = await cache.get("kiyasgo:products:abc123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_handles_exception(self):
        cache, mock_client = self._make_cache_with_mock()
        mock_client.get.side_effect = Exception("Connection error")

        result = await cache.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_success(self):
        cache, mock_client = self._make_cache_with_mock()

        result = await cache.set("key", {"score": 85}, ttl=7200)
        assert result is True
        mock_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_handles_exception(self):
        cache, mock_client = self._make_cache_with_mock()
        mock_client.setex.side_effect = Exception("Write error")

        result = await cache.set("key", {"data": 1})
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self):
        cache, mock_client = self._make_cache_with_mock()

        result = await cache.delete("key")
        assert result is True
        mock_client.delete.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_clear_namespace(self):
        cache, mock_client = self._make_cache_with_mock()
        mock_client.keys.return_value = ["kiyasgo:products:a", "kiyasgo:products:b"]

        count = await cache.clear_namespace("products")
        assert count == 2
        mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_namespace_empty(self):
        cache, mock_client = self._make_cache_with_mock()
        mock_client.keys.return_value = []

        count = await cache.clear_namespace("products")
        assert count == 0

    def test_make_key_deterministic(self):
        cache = RedisCache()
        key1 = cache._make_key("products", "samsung-s24")
        key2 = cache._make_key("products", "samsung-s24")
        assert key1 == key2
        assert key1.startswith("kiyasgo:products:")

    def test_make_key_different_args(self):
        cache = RedisCache()
        key1 = cache._make_key("products", "samsung-s24")
        key2 = cache._make_key("products", "iphone-16")
        assert key1 != key2
