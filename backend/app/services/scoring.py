"""
Itinerary Scoring & Ranking System

Implements weighted scoring to rank itineraries by price + safety + duration,
with configurable safety modes.
"""

import logging
from typing import Optional

from app.models import Itinerary, RiskLevel, SafetyMode, TravelDocs
from app.services.risk_engine import (
    CAUTION_TRANSIT_COUNTRIES,
    PREFERRED_TRANSIT_COUNTRIES,
    SCHENGEN_COUNTRIES,
    UK_COUNTRIES,
    has_relevant_travel_doc,
)

logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCORING WEIGHTS BY SAFETY MODE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SAFETY_MODE_WEIGHTS = {
    SafetyMode.PRICE_FIRST: {
        "price_weight": 1.0,
        "duration_weight": 0.10,
        "risk_multiplier": 0.6,
        "caution_multiplier": 0.8,
    },
    SafetyMode.BALANCED: {
        "price_weight": 1.0,
        "duration_weight": 0.15,
        "risk_multiplier": 1.0,
        "caution_multiplier": 1.0,
    },
    SafetyMode.SAFETY_FIRST: {
        "price_weight": 1.0,
        "duration_weight": 0.20,
        "risk_multiplier": 1.4,
        "caution_multiplier": 1.4,
    },
}

# Base penalties/bonuses (will be multiplied by safety mode multipliers)
STOPS_PENALTY_PER_STOP = 0.30
RISK_PENALTIES = {
    RiskLevel.LOW: 0.0,
    RiskLevel.MEDIUM: 1.0,
    RiskLevel.HIGH: 3.0,
}
CAUTION_COUNTRY_PENALTY = 1.5  # Per caution country
PREFERRED_COUNTRY_BONUS = -0.5  # Per preferred country
TRAVEL_DOC_BONUS = -0.3  # If relevant travel doc for caution/verify country


def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """
    Normalize a value to 0..1 range

    Args:
        value: Value to normalize
        min_val: Minimum value in dataset
        max_val: Maximum value in dataset

    Returns:
        Normalized value (0..1)
    """
    if max_val == min_val:
        return 0.0
    return (value - min_val) / (max_val - min_val)


def calculate_score(
    itinerary: Itinerary,
    safety_mode: SafetyMode,
    price_range: tuple[float, float],
    duration_range: tuple[int, int],
    travel_docs: Optional[TravelDocs] = None,
) -> float:
    """
    Calculate weighted score for an itinerary

    Lower score = better (more desirable)

    Args:
        itinerary: Flight itinerary
        safety_mode: Safety mode for weighting
        price_range: (min_price, max_price) in dataset
        duration_range: (min_duration, max_duration) in dataset
        travel_docs: Optional travel documents

    Returns:
        Score (lower is better)
    """
    weights = SAFETY_MODE_WEIGHTS[safety_mode]

    # 1. Normalized price component
    normalized_price = normalize_value(
        itinerary.price.total, price_range[0], price_range[1]
    )
    price_component = normalized_price * weights["price_weight"]

    # 2. Normalized duration component
    normalized_duration = normalize_value(
        itinerary.total_duration_minutes, duration_range[0], duration_range[1]
    )
    duration_component = normalized_duration * weights["duration_weight"]

    # 3. Stops penalty
    stops_penalty = itinerary.stops * STOPS_PENALTY_PER_STOP

    # 4. Risk penalty (adjusted by safety mode)
    base_risk_penalty = RISK_PENALTIES[itinerary.risk.level]
    risk_penalty = base_risk_penalty * weights["risk_multiplier"]

    # 5. Transit country penalties/bonuses
    transit_countries = set(itinerary.transit_countries)

    # Caution countries penalty
    caution_countries = transit_countries.intersection(CAUTION_TRANSIT_COUNTRIES)
    caution_penalty = len(caution_countries) * CAUTION_COUNTRY_PENALTY * weights[
        "caution_multiplier"
    ]

    # Preferred countries bonus
    preferred_countries = transit_countries.intersection(PREFERRED_TRANSIT_COUNTRIES)
    preferred_bonus = len(preferred_countries) * PREFERRED_COUNTRY_BONUS

    # Schengen/UK verification penalty (lighter than caution)
    schengen_countries = transit_countries.intersection(SCHENGEN_COUNTRIES)
    uk_countries = transit_countries.intersection(UK_COUNTRIES)
    verify_penalty = (len(schengen_countries) + len(uk_countries)) * 0.5 * weights[
        "caution_multiplier"
    ]

    # 6. Travel docs bonus
    travel_doc_bonus = 0.0
    if travel_docs:
        # Check if user has relevant docs for caution/verify countries
        relevant_countries = caution_countries.union(schengen_countries).union(uk_countries)
        for country in relevant_countries:
            has_doc, _ = has_relevant_travel_doc(country, travel_docs)
            if has_doc:
                travel_doc_bonus += TRAVEL_DOC_BONUS

    # Total score
    score = (
        price_component
        + duration_component
        + stops_penalty
        + risk_penalty
        + caution_penalty
        + verify_penalty
        + preferred_bonus
        + travel_doc_bonus
    )

    return score


def score_and_rank_itineraries(
    itineraries: list[Itinerary],
    safety_mode: SafetyMode,
    travel_docs: Optional[TravelDocs] = None,
) -> list[Itinerary]:
    """
    Score and rank itineraries by weighted score

    Args:
        itineraries: List of itineraries
        safety_mode: Safety mode for weighting
        travel_docs: Optional travel documents

    Returns:
        Sorted list of itineraries (best score first)
    """
    if not itineraries:
        return []

    # Calculate price and duration ranges
    prices = [it.price.total for it in itineraries]
    durations = [it.total_duration_minutes for it in itineraries]

    price_range = (min(prices), max(prices))
    duration_range = (min(durations), max(durations))

    # Calculate scores
    for itinerary in itineraries:
        itinerary.score = calculate_score(
            itinerary, safety_mode, price_range, duration_range, travel_docs
        )

    # Sort by score (lower is better)
    itineraries.sort(key=lambda x: x.score)

    logger.info(
        f"Scored and ranked {len(itineraries)} itineraries in {safety_mode.value} mode"
    )

    return itineraries
