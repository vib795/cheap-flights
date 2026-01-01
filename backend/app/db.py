import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.models import Itinerary, SearchRequest
from app.settings import settings

logger = logging.getLogger(__name__)

# Determine database type from URL
DATABASE_URL = settings.database_url
IS_POSTGRES = DATABASE_URL.startswith("postgresql")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

if IS_POSTGRES:
    import asyncpg

    _pool: Optional[asyncpg.Pool] = None
elif IS_SQLITE:
    import aiosqlite

    DB_PATH = Path("geoflight.db")
else:
    raise ValueError(f"Unsupported database URL: {DATABASE_URL}")


async def get_db_pool():
    """Get or create database connection pool (PostgreSQL only)"""
    global _pool
    if IS_POSTGRES:
        if _pool is None:
            # Extract connection parameters from URL
            # Format: postgresql+asyncpg://user:pass@host:port/dbname
            url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            _pool = await asyncpg.create_pool(url, min_size=2, max_size=10)
            logger.info("PostgreSQL connection pool created")
        return _pool
    return None


async def close_db_pool():
    """Close database connection pool (PostgreSQL only)"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL connection pool closed")


async def init_db():
    """Initialize database with required tables"""
    if IS_POSTGRES:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Searches table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS searches (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP NOT NULL,
                    request_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'completed'
                )
            """
            )

            # Itineraries table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS itineraries (
                    id TEXT PRIMARY KEY,
                    search_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    normalized_json TEXT NOT NULL,
                    price_total REAL NOT NULL,
                    currency TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    score REAL NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (search_id) REFERENCES searches (id)
                )
            """
            )

            # Provider payloads table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_payloads (
                    id SERIAL PRIMARY KEY,
                    itinerary_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    raw_json TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (itinerary_id) REFERENCES itineraries (id)
                )
            """
            )

            # Create indexes
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_itineraries_search_id ON itineraries(search_id)"
            )

            logger.info("PostgreSQL database initialized successfully")

    elif IS_SQLITE:
        async with aiosqlite.connect(DB_PATH) as db:
            # Searches table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS searches (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'completed'
                )
            """
            )

            # Itineraries table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS itineraries (
                    id TEXT PRIMARY KEY,
                    search_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    normalized_json TEXT NOT NULL,
                    price_total REAL NOT NULL,
                    currency TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    score REAL NOT NULL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (search_id) REFERENCES searches (id)
                )
            """
            )

            # Provider payloads table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_payloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    itinerary_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    raw_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (itinerary_id) REFERENCES itineraries (id)
                )
            """
            )

            # Create indexes
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_itineraries_search_id ON itineraries(search_id)"
            )

            await db.commit()
            logger.info("SQLite database initialized successfully")


def generate_cache_key(request: SearchRequest) -> str:
    """
    Generate cache key from search request

    Args:
        request: Search request

    Returns:
        Hash-based cache key
    """
    # Include travel docs in cache key
    travel_docs_str = ""
    if request.travel_docs:
        visas = ",".join(sorted(request.travel_docs.visas))
        residencies = ",".join(sorted(request.travel_docs.residencies))
        travel_docs_str = f"|visas:{visas}|res:{residencies}"

    key_data = (
        f"{request.origin}|{request.destination}|{request.date}|"
        f"{request.adults}|{request.cabin}|{request.max_stops}|"
        f"{request.passport_nationality}|{request.safety_mode}{travel_docs_str}"
    )
    return hashlib.sha256(key_data.encode()).hexdigest()


async def save_search(
    search_id: str, request: SearchRequest, itineraries: list[Itinerary]
) -> None:
    """
    Save search results to database for history/persistence

    Note: Caching is handled separately in app.cache module.
    This function only persists search history to the database.

    Args:
        search_id: Unique search ID
        request: Search request
        itineraries: List of itineraries
    """
    now = datetime.utcnow()

    if IS_POSTGRES:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Save search
                await conn.execute(
                    """
                    INSERT INTO searches (id, created_at, request_json, status)
                    VALUES ($1, $2, $3, $4)
                    """,
                    search_id,
                    now,
                    request.model_dump_json(),
                    "completed",
                )

                # Save itineraries
                for itinerary in itineraries:
                    await conn.execute(
                        """
                        INSERT INTO itineraries (
                            id, search_id, provider, normalized_json,
                            price_total, currency, risk_level, score, created_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        """,
                        itinerary.id,
                        search_id,
                        itinerary.provider,
                        itinerary.model_dump_json(),
                        itinerary.price.total,
                        itinerary.price.currency,
                        itinerary.risk.level.value,
                        itinerary.score,
                        now,
                    )

    elif IS_SQLITE:
        now_str = now.isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            # Save search
            await db.execute(
                """
                INSERT INTO searches (id, created_at, request_json, status)
                VALUES (?, ?, ?, ?)
                """,
                (search_id, now_str, request.model_dump_json(), "completed"),
            )

            # Save itineraries
            for itinerary in itineraries:
                await db.execute(
                    """
                    INSERT INTO itineraries (
                        id, search_id, provider, normalized_json,
                        price_total, currency, risk_level, score, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        itinerary.id,
                        search_id,
                        itinerary.provider,
                        itinerary.model_dump_json(),
                        itinerary.price.total,
                        itinerary.price.currency,
                        itinerary.risk.level.value,
                        itinerary.score,
                        now_str,
                    ),
                )

            await db.commit()

    logger.info(f"Saved search {search_id} with {len(itineraries)} itineraries")


async def get_search(search_id: str) -> Optional[dict[str, Any]]:
    """
    Retrieve search by ID

    Args:
        search_id: Search ID

    Returns:
        Search data with itineraries, or None if not found
    """
    if IS_POSTGRES:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get search
            search_row = await conn.fetchrow(
                """
                SELECT id, created_at, request_json, status
                FROM searches
                WHERE id = $1
                """,
                search_id,
            )

            if not search_row:
                return None

            # Get itineraries
            itinerary_rows = await conn.fetch(
                """
                SELECT normalized_json
                FROM itineraries
                WHERE search_id = $1
                ORDER BY score ASC
                """,
                search_id,
            )

            itineraries = [json.loads(row["normalized_json"]) for row in itinerary_rows]

            return {
                "search_id": search_row["id"],
                "request": json.loads(search_row["request_json"]),
                "itineraries": itineraries,
                "created_at": search_row["created_at"].isoformat(),
            }

    elif IS_SQLITE:
        async with aiosqlite.connect(DB_PATH) as db:
            # Get search
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, created_at, request_json, status
                FROM searches
                WHERE id = ?
                """,
                (search_id,),
            )
            search_row = await cursor.fetchone()

            if not search_row:
                return None

            # Get itineraries
            cursor = await db.execute(
                """
                SELECT normalized_json
                FROM itineraries
                WHERE search_id = ?
                ORDER BY score ASC
                """,
                (search_id,),
            )
            itinerary_rows = await cursor.fetchall()

            itineraries = [json.loads(row["normalized_json"]) for row in itinerary_rows]

            return {
                "search_id": search_row["id"],
                "request": json.loads(search_row["request_json"]),
                "itineraries": itineraries,
                "created_at": search_row["created_at"],
            }

    return None
