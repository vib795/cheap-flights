"""
Transit Safety & Visa Risk Engine (IN-first)

This module implements heuristic-based risk assessment for flight itineraries,
with a focus on Indian passport holders.

IMPORTANT: This is NOT authoritative visa/entry guidance. It's a best-effort
risk scoring system to help travelers identify potential issues that require
verification before booking.
"""

import logging
from datetime import datetime
from typing import Optional

from app.models import Itinerary, RiskAssessment, RiskLevel, TravelDocs

logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRANSIT POLICY LISTS (IN-FIRST) - EDITABLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Preferred transit hubs for Indian travelers (generally smoother airside connections)
# Still requires verification - these are heuristics
PREFERRED_TRANSIT_COUNTRIES = {
    "SG",  # Singapore
    "AE",  # UAE (Dubai, Abu Dhabi)
    "QA",  # Qatar (Doha)
    "OM",  # Oman
    "BH",  # Bahrain
    "SA",  # Saudi Arabia
    "TR",  # Turkey (Istanbul)
    "MY",  # Malaysia
    "TH",  # Thailand
    "HK",  # Hong Kong
    "JP",  # Japan
    "KR",  # South Korea
}

# Caution/high-friction transit countries for IN passport
# These often require transit visas or have complex requirements
CAUTION_TRANSIT_COUNTRIES = {
    "US",  # United States - often requires C-1 transit visa
    "CA",  # Canada - transit visa requirements
    "AU",  # Australia - electronic transit authority
}

# Schengen countries (verify-heavy for transit)
SCHENGEN_COUNTRIES = {
    "AT",  # Austria
    "BE",  # Belgium
    "CZ",  # Czech Republic
    "DK",  # Denmark
    "EE",  # Estonia
    "FI",  # Finland
    "FR",  # France
    "DE",  # Germany
    "GR",  # Greece
    "HU",  # Hungary
    "IS",  # Iceland
    "IT",  # Italy
    "LV",  # Latvia
    "LT",  # Lithuania
    "LU",  # Luxembourg
    "MT",  # Malta
    "NL",  # Netherlands
    "NO",  # Norway
    "PL",  # Poland
    "PT",  # Portugal
    "SK",  # Slovakia
    "SI",  # Slovenia
    "ES",  # Spain
    "SE",  # Sweden
    "CH",  # Switzerland
}

# UK - separate verification needed
UK_COUNTRIES = {"GB"}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# THRESHOLDS & CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MIN_SAFE_CONNECTION_INTERNATIONAL = 75  # minutes
LONG_LAYOVER_THRESHOLD = 8 * 60  # 8 hours
MEDIUM_LAYOVER_MIN = 3 * 60  # 3 hours
SHORT_LAYOVER_MAX = 3 * 60  # 3 hours


def is_overnight_layover(arrive_at: str, depart_at: str) -> bool:
    """Check if layover spans overnight (different calendar days)"""
    try:
        arr_dt = datetime.fromisoformat(arrive_at.replace("Z", "+00:00"))
        dep_dt = datetime.fromisoformat(depart_at.replace("Z", "+00:00"))
        return arr_dt.date() != dep_dt.date()
    except Exception as e:
        logger.warning(f"Failed to check overnight layover: {e}")
        return False


def has_relevant_travel_doc(
    country: str, travel_docs: Optional[TravelDocs]
) -> tuple[bool, str]:
    """
    Check if user has relevant travel document for a country

    Returns:
        (has_doc, doc_type) tuple
    """
    if not travel_docs:
        return False, ""

    # Check visas
    if country in travel_docs.visas or country.upper() in travel_docs.visas:
        return True, f"{country} visa"

    # Check special visa tokens
    if country in SCHENGEN_COUNTRIES and "SCHENGEN" in travel_docs.visas:
        return True, "Schengen visa"

    # Check residencies
    country_to_residency = {
        "US": ["US_GC", "US_PR", "US_RESIDENCE"],
        "CA": ["CA_PR", "CA_RESIDENCE"],
        "AU": ["AU_PR", "AU_RESIDENCE"],
        "GB": ["UK_BRP", "UK_ILR", "UK_RESIDENCE"],
    }

    # Check Schengen residency
    if country in SCHENGEN_COUNTRIES:
        for res in travel_docs.residencies:
            if "EU" in res or "SCHENGEN" in res:
                return True, "EU/Schengen residence permit"

    # Check country-specific residency
    residency_tokens = country_to_residency.get(country, [])
    for token in residency_tokens:
        if any(token in r.upper() for r in travel_docs.residencies):
            return True, f"{country} residence permit"

    return False, ""


def assess_risk(
    itinerary: Itinerary,
    passport_nationality: str,
    travel_docs: Optional[TravelDocs] = None,
) -> RiskAssessment:
    """
    Assess transit and visa risk for an itinerary (IN-first heuristics)

    Args:
        itinerary: Flight itinerary to assess
        passport_nationality: Passenger's passport country code
        travel_docs: Optional travel documents (visas/residencies)

    Returns:
        RiskAssessment with level, reasons, and verification steps
    """
    reasons: list[str] = []
    verify_steps: list[str] = []
    transit_countries: set[str] = set()
    layover_airports: list[str] = []

    # Collect transit countries and layover airports
    for layover in itinerary.layovers:
        layover_airports.append(layover.airport)
        if layover.country and layover.country != "UNKNOWN":
            transit_countries.add(layover.country)

    # Initialize risk level
    risk_level = RiskLevel.LOW

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HARD HIGH-RISK TRIGGERS (always HIGH, non-negotiable)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # 1. Airport change detection (rough heuristic)
    airport_change_detected = False
    for i in range(len(itinerary.segments) - 1):
        from_code = itinerary.segments[i].to_airport[:2]
        to_code = itinerary.segments[i + 1].from_airport[:2]
        if from_code == to_code and itinerary.segments[i].to_airport != itinerary.segments[
            i + 1
        ].from_airport:
            airport_change_detected = True
            reasons.append(
                f"⚠️ AIRPORT CHANGE: {itinerary.segments[i].to_airport} → "
                f"{itinerary.segments[i + 1].from_airport}"
            )
            verify_steps.append(
                "CRITICAL: Verify airport transfer logistics, visa requirements, and baggage re-check"
            )

    # 2. Overnight layover
    has_overnight = False
    for i, layover in enumerate(itinerary.layovers):
        if i < len(itinerary.segments) - 1:
            arrive = itinerary.segments[i].arrive_at
            depart = itinerary.segments[i + 1].depart_at
            if is_overnight_layover(arrive, depart):
                has_overnight = True
                reasons.append(
                    f"⚠️ OVERNIGHT layover at {layover.airport} "
                    f"({layover.minutes // 60}h {layover.minutes % 60}m)"
                )
                verify_steps.append(
                    f"Confirm if you can stay airside overnight at {layover.airport} "
                    f"or if you need a transit visa to exit"
                )

    # 3. Very long layovers (>8 hours)
    long_layovers = [lo for lo in itinerary.layovers if lo.minutes > LONG_LAYOVER_THRESHOLD]
    for layover in long_layovers:
        reasons.append(
            f"Very long layover at {layover.airport}: "
            f"{layover.minutes // 60}h {layover.minutes % 60}m"
        )
        verify_steps.append(
            f"Check if {layover.airport} allows airside stay for {layover.minutes // 60}+ hours "
            f"or requires exit/entry"
        )

    # 4. Tight connections (<75 min international)
    short_connections = [
        lo for lo in itinerary.layovers if lo.minutes < MIN_SAFE_CONNECTION_INTERNATIONAL
    ]
    if short_connections:
        for layover in short_connections:
            reasons.append(
                f"⚠️ TIGHT connection at {layover.airport}: only {layover.minutes} minutes"
            )
            verify_steps.append(
                f"Verify minimum connection time at {layover.airport} and check terminal/gate distances"
            )

    # Set to HIGH if any hard triggers found
    if airport_change_detected or has_overnight or long_layovers or short_connections:
        risk_level = RiskLevel.HIGH

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # POLICY-BASED RISK ADJUSTMENTS (IN-first)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    policy_risk_bump = 0  # 0=none, 1=medium, 2=high

    # Check CAUTION countries (US, CA, AU)
    caution_countries_present = transit_countries.intersection(CAUTION_TRANSIT_COUNTRIES)
    for country in sorted(caution_countries_present):
        has_doc, doc_type = has_relevant_travel_doc(country, travel_docs)
        if has_doc:
            reasons.append(
                f"Transiting {country} - user reports {doc_type} (still verify airside rules)"
            )
            verify_steps.append(
                f"Verify {country} transit rules with your {doc_type} - confirm airside vs landside"
            )
            # Reduce penalty but don't eliminate it
            if policy_risk_bump < 1:
                policy_risk_bump = 1
        else:
            reasons.append(
                f"⚠️ Transiting {country} - often requires transit visa for IN passport"
            )
            verify_steps.append(
                f"Check {country} transit visa requirements for Indian passport holders"
            )
            policy_risk_bump = 2  # Bump to HIGH

    # Check Schengen countries
    schengen_countries_present = transit_countries.intersection(SCHENGEN_COUNTRIES)
    if schengen_countries_present:
        schengen_list = ", ".join(sorted(schengen_countries_present))
        has_doc, doc_type = has_relevant_travel_doc(
            list(schengen_countries_present)[0], travel_docs
        )

        if has_doc:
            reasons.append(
                f"Transiting Schengen ({schengen_list}) - user reports {doc_type} (verify transit rules)"
            )
            verify_steps.append(
                "Verify Schengen airport transit visa (ATV) rules with your visa/permit"
            )
            if policy_risk_bump < 1:
                policy_risk_bump = 1
        else:
            reasons.append(
                f"Transiting Schengen ({schengen_list}) - verify airport transit visa (ATV) requirements"
            )
            verify_steps.append(
                "Check if you need Schengen Airport Transit Visa (ATV) for Indian passport"
            )
            if policy_risk_bump < 1:
                policy_risk_bump = 1

    # Check UK
    uk_countries_present = transit_countries.intersection(UK_COUNTRIES)
    if uk_countries_present:
        has_doc, doc_type = has_relevant_travel_doc("GB", travel_docs)
        if has_doc:
            reasons.append(
                f"Transiting UK - user reports {doc_type} (verify DATV/airside rules)"
            )
            verify_steps.append("Verify UK transit rules with your visa/permit - check DATV requirements")
            if policy_risk_bump < 1:
                policy_risk_bump = 1
        else:
            reasons.append("Transiting UK - verify Direct Airside Transit Visa (DATV) requirements")
            verify_steps.append(
                "Check if you need UK Direct Airside Transit Visa (DATV) for Indian passport"
            )
            if policy_risk_bump < 1:
                policy_risk_bump = 1

    # Apply policy-based risk bump
    if policy_risk_bump == 2 and risk_level != RiskLevel.HIGH:
        risk_level = RiskLevel.HIGH
    elif policy_risk_bump == 1 and risk_level == RiskLevel.LOW:
        risk_level = RiskLevel.MEDIUM

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MEDIUM-RISK TRIGGERS (if not already HIGH)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if risk_level != RiskLevel.HIGH:
        # Multiple stops (2+)
        if itinerary.stops >= 2:
            reasons.append(f"Multiple stops: {itinerary.stops} connections")
            verify_steps.append("Verify baggage is checked through to final destination")
            if risk_level == RiskLevel.LOW:
                risk_level = RiskLevel.MEDIUM

        # Medium-length layovers (3-8 hours)
        medium_layovers = [
            lo
            for lo in itinerary.layovers
            if MEDIUM_LAYOVER_MIN <= lo.minutes <= LONG_LAYOVER_THRESHOLD
        ]
        if medium_layovers:
            for layover in medium_layovers:
                reasons.append(
                    f"Medium layover at {layover.airport}: "
                    f"{layover.minutes // 60}h {layover.minutes % 60}m"
                )
            if risk_level == RiskLevel.LOW:
                risk_level = RiskLevel.MEDIUM

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PREFERRED TRANSIT BONUS (can reduce risk by one level)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    preferred_countries_present = transit_countries.intersection(PREFERRED_TRANSIT_COUNTRIES)
    if preferred_countries_present and not airport_change_detected and not has_overnight:
        # Only reduce if there are no hard triggers
        if risk_level == RiskLevel.HIGH and not short_connections and not long_layovers:
            risk_level = RiskLevel.MEDIUM
            reasons.append(
                f"Preferred transit hub(s): {', '.join(sorted(preferred_countries_present))}"
            )
        elif risk_level == RiskLevel.MEDIUM:
            # Can potentially reduce to LOW if only medium triggers
            if not caution_countries_present and not schengen_countries_present:
                risk_level = RiskLevel.LOW
                reasons.append(
                    f"Preferred transit hub(s): {', '.join(sorted(preferred_countries_present))}"
                )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DEFAULT VERIFY STEPS (always included)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    default_steps = [
        "Confirm this is a single ticket (not self-transfer)",
        "Confirm baggage is checked through to final destination",
        "Verify you can remain airside during all connections",
    ]

    for step in default_steps:
        if step not in verify_steps:
            verify_steps.append(step)

    # If no specific risks found, add a default reason
    if not reasons:
        reasons.append("No major risk factors identified")

    return RiskAssessment(
        level=risk_level,
        reasons=reasons,
        verify_steps=verify_steps,
        transit_countries=sorted(list(transit_countries)),
        layover_airports=layover_airports,
    )


def apply_risk_assessment(
    itineraries: list[Itinerary],
    passport_nationality: str,
    travel_docs: Optional[TravelDocs] = None,
) -> list[Itinerary]:
    """
    Apply risk assessment to all itineraries

    Args:
        itineraries: List of itineraries
        passport_nationality: Passenger's passport country code
        travel_docs: Optional travel documents

    Returns:
        Updated itineraries with risk assessments
    """
    for itinerary in itineraries:
        itinerary.risk = assess_risk(itinerary, passport_nationality, travel_docs)

    logger.info(f"Applied risk assessment to {len(itineraries)} itineraries")
    return itineraries
