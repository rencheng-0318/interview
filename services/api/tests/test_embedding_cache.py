"""Tests for the embedding cache."""

import pytest

from app.clients.embedding_cache import EmbeddingCache


@pytest.fixture
def cache():
    return EmbeddingCache(max_size=3)


def test_cache_miss_returns_none(cache: EmbeddingCache):
    assert cache.get("nonexistent") is None


def test_cache_put_and_get(cache: EmbeddingCache):
    vector = [0.1, 0.2, 0.3]
    cache.put("test query", vector)

    result = cache.get("test query")
    assert result == vector


def test_cache_updates_existing_entry(cache: EmbeddingCache):
    cache.put("query", [0.1, 0.2])
    cache.put("query", [0.3, 0.4])

    assert cache.get("query") == [0.3, 0.4]
    assert cache.size == 1


def test_cache_evicts_lru_when_full(cache: EmbeddingCache):
    cache.put("first", [1.0])
    cache.put("second", [2.0])
    cache.put("third", [3.0])
    assert cache.size == 3

    # Adding fourth should evict "first" (least recently used)
    cache.put("fourth", [4.0])
    assert cache.size == 3
    assert cache.get("first") is None
    assert cache.get("second") == [2.0]
    assert cache.get("third") == [3.0]
    assert cache.get("fourth") == [4.0]


def test_cache_access_refreshes_lru_order(cache: EmbeddingCache):
    cache.put("first", [1.0])
    cache.put("second", [2.0])
    cache.put("third", [3.0])

    # Access "first" to make it most recently used
    cache.get("first")

    # Now "second" is least recently used
    cache.put("fourth", [4.0])
    assert cache.get("second") is None
    assert cache.get("first") == [1.0]


def test_cache_tracks_hits_and_misses(cache: EmbeddingCache):
    cache.put("query", [1.0])

    cache.get("query")  # hit
    cache.get("query")  # hit
    cache.get("other")  # miss

    assert cache._hits == 2
    assert cache._misses == 1
    assert cache.hit_rate == pytest.approx(2 / 3)


def test_cache_stats(cache: EmbeddingCache):
    cache.put("a", [1.0])
    cache.get("a")  # hit
    cache.get("b")  # miss

    stats = cache.stats
    assert stats["size"] == 1
    assert stats["max_size"] == 3
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.5


def test_cache_clear(cache: EmbeddingCache):
    cache.put("a", [1.0])
    cache.put("b", [2.0])
    cache.get("a")

    cache.clear()

    assert cache.size == 0
    assert cache._hits == 0
    assert cache._misses == 0
    assert cache.get("a") is None


def test_cache_get_put_workflow(cache: EmbeddingCache):
    """Verify the get/put pattern used by the search service."""
    # Simulate: check cache -> miss -> compute -> store
    assert cache.get("hello") is None
    cache.put("hello", [5.0])

    # Second lookup hits cache
    assert cache.get("hello") == [5.0]
    assert cache._hits == 1
    assert cache._misses == 1

    # Different text is a miss
    assert cache.get("world!") is None
    cache.put("world!", [6.0])
    assert cache.get("world!") == [6.0]
