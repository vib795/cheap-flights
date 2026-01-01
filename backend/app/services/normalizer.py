import hashlib
import logging
from datetime import datetime
from typing import Any

from app.models import FlightSegment, Itinerary, Layover, Price

logger = logging.getLogger(__name__)

# Simple mapping of airport codes to country codes (subset for MVP)
# In production, use a proper airport database
AIRPORT_TO_COUNTRY = {
    "JFK": "US",
    "EWR": "US",
    "LAX": "US",
    "ORD": "US",
    "SFO": "US",
    "DFW": "US",
    "ATL": "US",
    "IAH": "US",
    "MIA": "US",
    "LHR": "GB",
    "LGW": "GB",
    "CDG": "FR",
    "AMS": "NL",
    "FRA": "DE",
    "MUC": "DE",
    "MAD": "ES",
    "BCN": "ES",
    "FCO": "IT",
    "MXP": "IT",
    "DXB": "AE",
    "DOH": "QA",
    "IST": "TR",
    "SIN": "SG",
    "HKG": "HK",
    "NRT": "JP",
    "HND": "JP",
    "ICN": "KR",
    "BKK": "TH",
    "DEL": "IN",
    "BOM": "IN",
    "SYD": "AU",
    "YYZ": "CA",
    "YVR": "CA",
    "MEX": "MX",
    "GRU": "BR",
    "EZE": "AR",
}


def get_country_from_airport(iata: str) -> str:
    """Get country code from airport IATA code (best effort)"""
    return AIRPORT_TO_COUNTRY.get(iata.upper(), "UNKNOWN")


def parse_duration(iso_duration: str) -> int:
    """
    Parse ISO 8601 duration to minutes
    Example: PT2H30M -> 150 minutes
    """
    if not iso_duration or not iso_duration.startswith("PT"):
        return 0

    duration = iso_duration[2:]  # Remove PT prefix
    hours = 0
    minutes = 0

    if "H" in duration:
        parts = duration.split("H")
        hours = int(parts[0])
        duration = parts[1] if len(parts) > 1 else ""

    if "M" in duration:
        minutes = int(duration.replace("M", ""))

    return hours * 60 + minutes


def normalize_amadeus_offer(offer: dict[str, Any]) -> Itinerary:
    """
    Normalize an Amadeus flight offer to internal Itinerary schema

    Args:
        offer: Raw Amadeus flight offer dictionary

    Returns:
        Normalized Itinerary object
    """
    # Generate unique ID from offer data
    offer_id = offer.get("id", hashlib.md5(str(offer).encode()).hexdigest())

    # Extract price
    price_data = offer.get("price", {})
    price = Price(
        total=float(price_data.get("grandTotal", 0)),
        currency=price_data.get("currency", "USD"),
    )

    # Parse itineraries (usually one for one-way)
    itineraries = offer.get("itineraries", [])
    if not itineraries:
        raise ValueError("No itineraries in offer")

    itinerary_data = itineraries[0]
    segments_data = itinerary_data.get("segments", [])

    # Parse segments
    segments: list[FlightSegment] = []
    for seg in segments_data:
        departure = seg.get("departure", {})
        arrival = seg.get("arrival", {})
        carrier_code = seg.get("carrierCode", "")
        flight_number = seg.get("number", "")

        segments.append(
            FlightSegment(
                carrier=carrier_code,
                flight_number=f"{carrier_code}{flight_number}",
                from_airport=departure.get("iataCode", ""),
                to_airport=arrival.get("iataCode", ""),
                depart_at=departure.get("at", ""),
                arrive_at=arrival.get("at", ""),
                duration_minutes=parse_duration(seg.get("duration", "")),
            )
        )

    # Calculate layovers
    layovers: list[Layover] = []
    for i in range(len(segments) - 1):
        current_arrival = segments[i].arrive_at
        next_departure = segments[i + 1].depart_at
        layover_airport = segments[i].to_airport

        if current_arrival and next_departure:
            try:
                arr_dt = datetime.fromisoformat(current_arrival.replace("Z", "+00:00"))
                dep_dt = datetime.fromisoformat(next_departure.replace("Z", "+00:00"))
                layover_minutes = int((dep_dt - arr_dt).total_seconds() / 60)

                layovers.append(
                    Layover(
                        airport=layover_airport,
                        minutes=layover_minutes,
                        country=get_country_from_airport(layover_airport),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to calculate layover: {e}")

    # Calculate total duration
    total_duration = parse_duration(itinerary_data.get("duration", ""))

    # Count stops
    stops = len(segments) - 1

    # Extract transit countries from layovers
    transit_countries = []
    for layover in layovers:
        if layover.country and layover.country != "UNKNOWN":
            if layover.country not in transit_countries:
                transit_countries.append(layover.country)

    # Create placeholder risk assessment (will be filled by risk engine)
    from app.models import RiskAssessment, RiskLevel

    risk = RiskAssessment(
        level=RiskLevel.LOW,
        reasons=[],
        verify_steps=[],
        transit_countries=[],
        layover_airports=[],
    )

    return Itinerary(
        id=offer_id,
        provider="amadeus",
        price=price,
        total_duration_minutes=total_duration,
        stops=stops,
        segments=segments,
        layovers=layovers,
        transit_countries=transit_countries,
        risk=risk,
        raw_provider_payload_ref=f"amadeus:{offer_id}",
    )


def normalize_amadeus_offers(offers: list[dict[str, Any]]) -> list[Itinerary]:
    """
    Normalize multiple Amadeus offers

    Args:
        offers: List of raw Amadeus offers

    Returns:
        List of normalized Itinerary objects
    """
    itineraries: list[Itinerary] = []

    for offer in offers:
        try:
            itinerary = normalize_amadeus_offer(offer)
            itineraries.append(itinerary)
        except Exception as e:
            logger.error(f"Failed to normalize offer: {e}")
            continue

    logger.info(f"Normalized {len(itineraries)}/{len(offers)} offers")
    return itineraries
