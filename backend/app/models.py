from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class CabinClass(str, Enum):
    """Flight cabin class options"""

    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"


class RiskLevel(str, Enum):
    """Transit/visa risk levels"""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SafetyMode(str, Enum):
    """Safety mode for scoring/ranking"""

    PRICE_FIRST = "price_first"
    BALANCED = "balanced"
    SAFETY_FIRST = "safety_first"


# Request/Response Models


class TravelDocs(BaseModel):
    """Optional travel documents (visas, residencies)"""

    visas: list[str] = Field(
        default_factory=list,
        description="Visa countries (e.g. US, SCHENGEN, UK, CA, AU)",
    )
    residencies: list[str] = Field(
        default_factory=list,
        description="Residency permits (e.g. US_GC, UK_BRP, EU_PR)",
    )
    notes: str = Field(default="", description="Optional free text notes")


class SearchRequest(BaseModel):
    """Flight search request"""

    origin: str = Field(..., description="Origin airport IATA code (e.g. AUS)")
    destination: str = Field(..., description="Destination airport IATA code (e.g. DEL)")
    date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    adults: int = Field(default=1, ge=1, le=9, description="Number of adult passengers")
    cabin: CabinClass = Field(default=CabinClass.ECONOMY, description="Cabin class")
    max_stops: int = Field(default=2, ge=0, le=2, description="Maximum number of stops")
    passport_nationality: str = Field(
        default="IN", description="Passport country ISO code (default IN)"
    )
    safety_mode: SafetyMode = Field(
        default=SafetyMode.BALANCED, description="Safety mode for ranking"
    )
    travel_docs: Optional[TravelDocs] = Field(
        None, description="Optional travel documents (visas/residencies)"
    )
    flex_days: int = Field(default=0, ge=0, le=3, description="Flexible dates +/- days")


class FlightSegment(BaseModel):
    """Single flight segment"""

    carrier: str = Field(..., description="Airline IATA code")
    flight_number: str = Field(..., description="Flight number")
    from_airport: str = Field(..., alias="from", description="Departure airport IATA")
    to_airport: str = Field(..., alias="to", description="Arrival airport IATA")
    depart_at: str = Field(..., description="Departure datetime ISO format")
    arrive_at: str = Field(..., description="Arrival datetime ISO format")
    duration_minutes: int = Field(..., description="Flight duration in minutes")

    class Config:
        populate_by_name = True


class Layover(BaseModel):
    """Layover information"""

    airport: str = Field(..., description="Layover airport IATA code")
    minutes: int = Field(..., description="Layover duration in minutes")
    country: Optional[str] = Field(None, description="Country ISO code if known")


class RiskAssessment(BaseModel):
    """Transit/visa risk assessment"""

    level: RiskLevel = Field(..., description="Overall risk level")
    reasons: list[str] = Field(default_factory=list, description="Risk factors identified")
    verify_steps: list[str] = Field(
        default_factory=list, description="Verification steps for traveler"
    )
    transit_countries: list[str] = Field(
        default_factory=list, description="Countries transited through"
    )
    layover_airports: list[str] = Field(
        default_factory=list, description="Layover airports"
    )


class VisaBaseline(BaseModel):
    """Baseline visa/entry information"""

    destination_entry_summary: str = Field(
        default="Unknown", description="Entry requirements summary"
    )
    source: str = Field(default="travelbriefing", description="Data source")
    disclaimer: str = Field(
        default="Best-effort information; verify with official sources before booking.",
        description="Disclaimer text",
    )


class Price(BaseModel):
    """Price information"""

    total: float = Field(..., description="Total price")
    currency: str = Field(..., description="Currency code (e.g. USD)")


class Itinerary(BaseModel):
    """Flight itinerary with risk assessment"""

    id: str = Field(..., description="Unique itinerary ID")
    provider: str = Field(default="amadeus", description="Data provider")
    price: Price = Field(..., description="Price details")
    total_duration_minutes: int = Field(..., description="Total journey duration")
    stops: int = Field(..., description="Number of stops")
    segments: list[FlightSegment] = Field(..., description="Flight segments")
    layovers: list[Layover] = Field(default_factory=list, description="Layover details")
    transit_countries: list[str] = Field(
        default_factory=list, description="Countries transited through"
    )
    risk: RiskAssessment = Field(..., description="Risk assessment")
    visa_baseline: Optional[VisaBaseline] = Field(None, description="Visa baseline info")
    score: float = Field(default=0.0, description="Ranking score (lower is better)")
    raw_provider_payload_ref: Optional[str] = Field(
        None, description="Reference to raw provider data"
    )


class SearchMeta(BaseModel):
    """Search metadata"""

    provider: str = Field(default="amadeus", description="Primary data provider")
    cached: bool = Field(default=False, description="Whether results were cached")
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(), description="Generation timestamp"
    )


class SearchResponse(BaseModel):
    """Flight search response"""

    search_id: str = Field(..., description="Unique search ID")
    query: SearchRequest = Field(..., description="Original search query")
    results: list[Itinerary] = Field(..., description="Search results")
    meta: SearchMeta = Field(..., description="Metadata")


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(default="healthy", description="Service status")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(), description="Current timestamp"
    )
