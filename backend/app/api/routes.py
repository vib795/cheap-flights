import hashlib
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from app import db
from app.models import (
    HealthResponse,
    Itinerary,
    SearchMeta,
    SearchRequest,
    SearchResponse,
)
from app.services.amadeus import amadeus_client
from app.services.normalizer import get_country_from_airport, normalize_amadeus_offers
from app.services.risk_engine import apply_risk_assessment
from app.services.scoring import score_and_rank_itineraries
from app.services.travelbriefing import travelbriefing_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", timestamp=datetime.utcnow().isoformat())


@router.post("/search", response_model=SearchResponse)
async def search_flights(request: SearchRequest):
    """
    Search for flights with visa/transit risk assessment and smart ranking

    Args:
        request: Flight search parameters

    Returns:
        SearchResponse with itineraries ranked by price + safety
    """
    logger.info(
        f"Search request: {request.origin} -> {request.destination} on {request.date} "
        f"(passport: {request.passport_nationality}, mode: {request.safety_mode.value})"
    )

    # Check cache
    cached_search_id = await db.get_cached_search(request)
    if cached_search_id:
        cached_data = await db.get_search(cached_search_id)
        if cached_data:
            logger.info(f"Returning cached results for search {cached_search_id}")
            return SearchResponse(
                search_id=cached_search_id,
                query=request,
                results=[Itinerary(**it) for it in cached_data["itineraries"]],
                meta=SearchMeta(provider="amadeus", cached=True),
            )

    try:
        # Search flights using Amadeus
        logger.info("Fetching flight offers from Amadeus...")
        raw_offers = await amadeus_client.search_flights(request)

        if not raw_offers:
            logger.warning("No flight offers found")
            return SearchResponse(
                search_id=_generate_search_id(),
                query=request,
                results=[],
                meta=SearchMeta(provider="amadeus", cached=False),
            )

        # Normalize to internal schema
        logger.info(f"Normalizing {len(raw_offers)} offers...")
        itineraries = normalize_amadeus_offers(raw_offers)

        # Apply risk assessment with IN-first policies and travel docs
        logger.info("Applying risk assessment...")
        itineraries = apply_risk_assessment(
            itineraries, request.passport_nationality, request.travel_docs
        )

        # Get visa baseline info for destination
        destination_country = "UNKNOWN"
        if itineraries and itineraries[0].segments:
            dest_airport = itineraries[0].segments[-1].to_airport
            destination_country = get_country_from_airport(dest_airport)

        if destination_country != "UNKNOWN":
            logger.info(f"Fetching visa baseline for {destination_country}...")
            visa_baseline = await travelbriefing_client.get_visa_info(
                destination_country, request.passport_nationality
            )

            # Attach visa baseline to all itineraries
            for itinerary in itineraries:
                itinerary.visa_baseline = visa_baseline

        # Score and rank by safety mode
        logger.info(f"Scoring and ranking in {request.safety_mode.value} mode...")
        itineraries = score_and_rank_itineraries(
            itineraries, request.safety_mode, request.travel_docs
        )

        # Take top 20
        top_itineraries = itineraries[:20]

        # Generate search ID and save to database
        search_id = _generate_search_id()
        await db.save_search(search_id, request, top_itineraries)

        logger.info(f"Search completed successfully with {len(top_itineraries)} results")

        return SearchResponse(
            search_id=search_id,
            query=request,
            results=top_itineraries,
            meta=SearchMeta(provider="amadeus", cached=False),
        )

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Flight search failed: {str(e)}")


@router.get("/search/{search_id}", response_model=SearchResponse)
async def get_search_results(search_id: str):
    """
    Retrieve previously executed search by ID

    Args:
        search_id: Search ID

    Returns:
        SearchResponse with stored results
    """
    logger.info(f"Retrieving search {search_id}")

    search_data = await db.get_search(search_id)

    if not search_data:
        raise HTTPException(status_code=404, detail=f"Search {search_id} not found")

    return SearchResponse(
        search_id=search_data["search_id"],
        query=SearchRequest(**search_data["request"]),
        results=[Itinerary(**it) for it in search_data["itineraries"]],
        meta=SearchMeta(provider="amadeus", cached=True),
    )


def _generate_search_id() -> str:
    """Generate unique search ID"""
    timestamp = datetime.utcnow().isoformat()
    return hashlib.sha256(timestamp.encode()).hexdigest()[:16]
