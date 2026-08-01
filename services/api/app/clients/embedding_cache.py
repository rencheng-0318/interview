"""Async-safe LRU cache for query embedding vectors.

Caches text -> embedding vector mappings to avoid redundant calls to the
embedding service. Since embeddings are deterministic (same text always
produces same vector), no TTL is needed.
"""

import logging
from collections import OrderedDict
from dataclasses import dataclass, field

logger = logging.getLogger("api.embedding_cache")


@dataclass
class EmbeddingCache:
    """Thread-safe LRU cache for embedding vectors.

    Since asyncio is single-threaded, dict operations are inherently safe
    without explicit locking.
    """

    max_size: int = 1000
    _cache: OrderedDict[str, list[float]] = field(default_factory=OrderedDict, init=False)
    _hits: int = field(default=0, init=False)
    _misses: int = field(default=0, init=False)

    def get(self, text: str) -> list[float] | None:
        """Get cached embedding vector for text. Returns None if not cached."""
        if text in self._cache:
            self._hits += 1
            # Move to end (most recently used)
            self._cache.move_to_end(text)
            return self._cache[text]
        self._misses += 1
        return None

    def put(self, text: str, vector: list[float]) -> None:
        """Cache an embedding vector, evicting LRU entry if at capacity."""
        if text in self._cache:
            # Update existing entry
            self._cache[text] = vector
            self._cache.move_to_end(text)
        else:
            if len(self._cache) >= self.max_size:
                # Evict least recently used
                evicted_key, _ = self._cache.popitem(last=False)
                logger.debug("embedding_cache evicted key=%s", evicted_key[:50])
            self._cache[text] = vector

    def get_or_compute_sync(self, text: str, compute_fn) -> list[float]:
        """Get from cache or compute synchronously."""
        cached = self.get(text)
        if cached is not None:
            return cached
        vector = compute_fn(text)
        self.put(text, vector)
        return vector

    async def get_or_compute(self, text: str, compute_fn) -> list[float]:
        """Get from cache or compute asynchronously."""
        cached = self.get(text)
        if cached is not None:
            return cached
        vector = await compute_fn(text)
        self.put(text, vector)
        return vector

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> dict:
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate, 4),
        }

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("embedding_cache cleared")
