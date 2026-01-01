"""Tests for the scoring module"""

import pytest

from app.models import (
    FlightSegment,
    Itinerary,
    Layover,
    Price,
    RiskAssessment,
    RiskLevel,
    SafetyMode,
    TravelDocs,
)
from app.services.scoring import score_and_rank_itineraries


def create_test_itinerary(
    price: float,
    duration: int,
    risk_level: RiskLevel,
    transit_countries: list[str],
) -> Itinerary:
    """Helper to create test itinerary"""
    return Itinerary(
        id=f"test_{price}",
        provider="test",
        price=Price(total=price, currency="USD"),
        total_duration_minutes=duration,
        stops=len(transit_countries),
        segments=[
            FlightSegment(
                carrier="AA",
                flight_number="AA100",
                from_airport="DEL",
                to_airport="SFO",
                depart_at="2026-02-10T10:00:00",
                arrive_at="2026-02-10T14:00:00",
                duration_minutes=duration,
            )
        ],
        layovers=[],
        transit_countries=transit_countries,
        risk=RiskAssessment(
            level=risk_level,
            reasons=[],
            verify_steps=[],
            transit_countries=transit_countries,
            layover_airports=[],
        ),
    )


def test_price_first_mode_prioritizes_price():
    """Test that price_first mode ranks cheaper flights higher"""
    itineraries = [
        create_test_itinerary(2000, 1000, RiskLevel.HIGH, ["US"]),  # Cheap but risky
        create_test_itinerary(3000, 800, RiskLevel.LOW, ["SG"]),  # Expensive but safe
    ]

    ranked = score_and_rank_itineraries(itineraries, SafetyMode.PRICE_FIRST)

    # In price_first mode, cheaper flight should rank higher despite HIGH risk
    assert ranked[0].price.total < ranked[1].price.total


def test_safety_first_mode_prioritizes_safety():
    """Test that safety_first mode ranks safer flights higher"""
    itineraries = [
        create_test_itinerary(2000, 1000, RiskLevel.HIGH, ["US"]),  # Cheap but risky
        create_test_itinerary(2100, 1000, RiskLevel.LOW, ["SG"]),  # Slightly more but safe
    ]

    ranked = score_and_rank_itineraries(itineraries, SafetyMode.SAFETY_FIRST)

    # In safety_first mode, safer flight should rank higher despite higher price
    assert ranked[0].risk.level == RiskLevel.LOW
    assert ranked[1].risk.level == RiskLevel.HIGH


def test_balanced_mode():
    """Test that balanced mode balances price and safety"""
    itineraries = [
        create_test_itinerary(2000, 1000, RiskLevel.HIGH, ["US"]),
        create_test_itinerary(2500, 900, RiskLevel.MEDIUM, ["DE"]),
        create_test_itinerary(3000, 800, RiskLevel.LOW, ["SG"]),
    ]

    ranked = score_and_rank_itineraries(itineraries, SafetyMode.BALANCED)

    # Medium risk with reasonable price should be in the middle
    assert ranked[1].risk.level == RiskLevel.MEDIUM


def test_preferred_transit_bonus():
    """Test that preferred transit countries get bonus"""
    itineraries = [
        create_test_itinerary(2000, 1000, RiskLevel.MEDIUM, ["US"]),  # Caution country
        create_test_itinerary(2000, 1000, RiskLevel.MEDIUM, ["SG"]),  # Preferred country
    ]

    ranked = score_and_rank_itineraries(itineraries, SafetyMode.BALANCED)

    # Preferred transit should rank higher
    assert "SG" in ranked[0].transit_countries


def test_travel_docs_improve_ranking():
    """Test that relevant travel docs improve ranking"""
    itineraries = [
        create_test_itinerary(2000, 1000, RiskLevel.HIGH, ["US"]),
    ]

    # Without travel docs
    ranked_without = score_and_rank_itineraries(itineraries.copy(), SafetyMode.BALANCED)
    score_without = ranked_without[0].score

    # With US visa
    travel_docs = TravelDocs(visas=["US"], residencies=[], notes="")
    ranked_with = score_and_rank_itineraries(
        itineraries.copy(), SafetyMode.BALANCED, travel_docs
    )
    score_with = ranked_with[0].score

    # Score should be better (lower) with travel docs
    assert score_with < score_without


def test_scoring_produces_consistent_results():
    """Test that scoring is deterministic"""
    itineraries = [
        create_test_itinerary(2000, 1000, RiskLevel.MEDIUM, ["SG"]),
        create_test_itinerary(2500, 900, RiskLevel.LOW, ["AE"]),
    ]

    ranked1 = score_and_rank_itineraries(itineraries.copy(), SafetyMode.BALANCED)
    ranked2 = score_and_rank_itineraries(itineraries.copy(), SafetyMode.BALANCED)

    # Should produce same ranking
    assert ranked1[0].id == ranked2[0].id
    assert ranked1[1].id == ranked2[1].id
