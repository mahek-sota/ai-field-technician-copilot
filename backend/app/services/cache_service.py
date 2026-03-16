"""
CacheService — in-memory TTL cache with generic string keys.

Design:
  - Keyed by arbitrary string (e.g. "diagnosis:{machine_id}").
  - Each entry stores (value, expiry_timestamp).
  - Thread-safe for single-process use (no async locking needed for dict ops in CPython).
  - TTL defaults to settings.CACHE_TTL_SECONDS; can be overridden per-call.
"""
import time
from typing import Any, Dict, Optional, Tuple

from app.config import settings


class CacheService:
    def __init__(self, ttl_seconds: Optional[int] = None):
        self._default_ttl = ttl_seconds if ttl_seconds is not None else settings.CACHE_TTL_SECONDS
        self._store: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if present and not expired, else None."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if time.time() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value with TTL expiry."""
        ttl_seconds = ttl if ttl is not None else self._default_ttl
        self._store[key] = (value, time.time() + ttl_seconds)

    def invalidate(self, key: str) -> None:
        """Remove a specific cache entry."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Flush all cache entries (useful in tests)."""
        self._store.clear()

    def size(self) -> int:
        """Return number of live (non-expired) entries."""
        now = time.time()
        return sum(1 for _, (_, exp) in self._store.items() if exp > now)
