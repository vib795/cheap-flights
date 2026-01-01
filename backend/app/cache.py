"""
Cache for search result deduplication

This module provides a TTL-based cache for flight search results.
- If REDIS_URL is configured: uses Redis (distributed, multi-worker safe)
- Otherwise: uses in-memory dict (single-worker only)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.settings import settings

logger = logging.getLogger(__name__)

# Try to import redis, but don't fail if not available
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis package not available, falling back to in-memory cache")


class SimpleCache:
    """
    In-memory cache with TTL support

    Thread-safe for async use since we're using asyncio (single-threaded event loop).
    For multi-process deployment, use RedisCache instead.
    """

    def __init__(self, default_ttl_seconds: int = 1800):
        """
        Initialize cache

        Args:
            default_ttl_seconds: Default TTL in seconds (default: 30 minutes)
        """
        self._store: dict[str, tuple[str, datetime]] = {}  # key -> (value, expires_at)
        self.default_ttl_seconds = default_ttl_seconds

    async def get(self, key: str) -> Optional[str]:
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

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
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

    async def delete(self, key: str) -> None:
        """Delete key from cache"""
        if key in self._store:
            del self._store[key]
            logger.info(f"Deleted key {key[:8]}... from cache")

    async def clear(self) -> None:
        """Clear all cache entries"""
        count = len(self._store)
        self._store.clear()
        logger.info(f"Cleared {count} entries from cache")

    async def cleanup_expired(self) -> int:
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

    async def size(self) -> int:
        """Get current cache size"""
        return len(self._store)


class RedisCache:
    """
    Redis-backed cache with TTL support

    Multi-process safe, suitable for production deployments.
    """

    def __init__(self, redis_url: str, default_ttl_seconds: int = 1800):
        """
        Initialize Redis cache

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            default_ttl_seconds: Default TTL in seconds (default: 30 minutes)
        """
        self.redis_url = redis_url
        self.default_ttl_seconds = default_ttl_seconds
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
        return self._client

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if missing/expired
        """
        try:
            client = await self._get_client()
            value = await client.get(key)

            if value is None:
                logger.info(f"Cache miss for key {key[:8]}...")
                return None

            logger.info(f"Cache hit for key {key[:8]}...")
            return value

        except Exception as e:
            logger.error(f"Redis GET error for key {key[:8]}: {e}")
            return None

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in Redis cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (uses default if None)
        """
        try:
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
            client = await self._get_client()
            await client.setex(key, ttl, value)
            logger.info(f"Cached key {key[:8]}... in Redis with TTL {ttl}s")

        except Exception as e:
            logger.error(f"Redis SET error for key {key[:8]}: {e}")

    async def delete(self, key: str) -> None:
        """Delete key from Redis cache"""
        try:
            client = await self._get_client()
            await client.delete(key)
            logger.info(f"Deleted key {key[:8]}... from Redis")

        except Exception as e:
            logger.error(f"Redis DELETE error for key {key[:8]}: {e}")

    async def clear(self) -> None:
        """Clear all cache entries (use with caution!)"""
        try:
            client = await self._get_client()
            await client.flushdb()
            logger.info("Cleared all entries from Redis")

        except Exception as e:
            logger.error(f"Redis FLUSHDB error: {e}")

    async def cleanup_expired(self) -> int:
        """
        Redis automatically removes expired keys, so this is a no-op

        Returns:
            Always returns 0
        """
        # Redis handles expiration automatically
        return 0

    async def size(self) -> int:
        """Get current cache size"""
        try:
            client = await self._get_client()
            return await client.dbsize()

        except Exception as e:
            logger.error(f"Redis DBSIZE error: {e}")
            return 0

    async def close(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.close()


def create_cache():
    """
    Factory function to create appropriate cache based on configuration

    Returns:
        RedisCache if redis_url is configured, otherwise SimpleCache
    """
    if settings.redis_url and REDIS_AVAILABLE:
        logger.info(f"Initializing Redis cache: {settings.redis_url}")
        return RedisCache(settings.redis_url, settings.app_cache_ttl_seconds)
    else:
        if settings.redis_url and not REDIS_AVAILABLE:
            logger.warning(
                "REDIS_URL configured but redis package not available, using in-memory cache"
            )
        logger.info("Initializing in-memory cache (single-worker only)")
        return SimpleCache(settings.app_cache_ttl_seconds)


# Global cache instance
search_cache = create_cache()
