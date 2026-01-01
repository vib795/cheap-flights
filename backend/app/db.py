import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import aiosqlite

from app.models import Itinerary, SearchRequest, SearchResponse
from app.settings import settings

logger = logging.getLogger(__name__)

DB_PATH = Path("geoflight.db")


async def init_db():
    """Initialize database with required tables"""
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
        logger.info("Database initialized successfully")


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

    Note: Caching is handled separately in app.cache module (in-memory).
    This function only persists search history to the database.

    Args:
        search_id: Unique search ID
        request: Search request
        itineraries: List of itineraries
    """
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        # Save search
        await db.execute(
            """
            INSERT INTO searches (id, created_at, request_json, status)
            VALUES (?, ?, ?, ?)
            """,
            (search_id, now, request.model_dump_json(), "completed"),
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
                    now,
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


