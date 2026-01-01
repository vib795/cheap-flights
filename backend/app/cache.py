"""
Simple in-memory cache for search result deduplication

This module provides a lightweight TTL-based cache for flight search results.
For MVP, we use an in-process dict. For production, upgrade to Redis.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    In-memory cache with TTL support

    Thread-safe for async use since we're using asyncio (single-threaded event loop).
    For multi-process deployment, use Redis instead.
    """

    def __init__(self, default_ttl_seconds: int = 1800):
        """
        Initialize cache

        Args:
            default_ttl_seconds: Default TTL in seconds (default: 30 minutes)
        """
        self._store: dict[str, tuple[str, datetime]] = {}  # key -> (value, expires_at)
        self.default_ttl_seconds = default_ttl_seconds

    def get(self, key: str) -> Optional[str]:
        """
        Get value from cache if not expired

        Args:
            key: Cache key

        Returns:
            Cached value or None if missing/expired
        """
        if key not in self._store:
            logger.info(f"Cache miss for key {key[:8]}...")
            return None

        value, expires_at = self._store[key]

        if datetime.utcnow() > expires_at:
            # Expired, remove it
            del self._store[key]
            logger.info(f"Cache expired for key {key[:8]}...")
            return None

        logger.info(f"Cache hit for key {key[:8]}...")
        return value

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (uses default if None)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self._store[key] = (value, expires_at)
        logger.info(f"Cached key {key[:8]}... with TTL {ttl}s")

    def delete(self, key: str) -> None:
        """Delete key from cache"""
        if key in self._store:
            del self._store[key]
            logger.info(f"Deleted key {key[:8]}... from cache")

    def clear(self) -> None:
        """Clear all cache entries"""
        count = len(self._store)
        self._store.clear()
        logger.info(f"Cleared {count} entries from cache")

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries

        Returns:
            Number of entries removed
        """
        now = datetime.utcnow()
        expired_keys = [
            key for key, (_, expires_at) in self._store.items() if now > expires_at
        ]

        for key in expired_keys:
            del self._store[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def size(self) -> int:
        """Get current cache size"""
        return len(self._store)


# Global cache instance
search_cache = SimpleCache(default_ttl_seconds=1800)  # 30 minutes
