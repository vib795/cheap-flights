"""Tests for the risk engine module"""

import pytest
from datetime import datetime, timedelta

from app.models import (
    FlightSegment,
    Itinerary,
    Layover,
    Price,
    RiskAssessment,
    RiskLevel,
    TravelDocs,
)
from app.services.risk_engine import assess_risk


def create_test_itinerary(
    layovers: list[Layover],
    segments: list[FlightSegment] | None = None,
) -> Itinerary:
    """Helper to create test itinerary"""
    if segments is None:
        # Create default segments based on layovers
        segments = [
            FlightSegment(
                carrier="AA",
                flight_number="AA100",
                from_airport="DEL",
                to_airport=layovers[0].airport if layovers else "SFO",
                depart_at="2026-02-10T10:00:00",
                arrive_at="2026-02-10T14:00:00",
                duration_minutes=240,
            )
        ]

    transit_countries = [lo.country for lo in layovers if lo.country]

    return Itinerary(
        id="test123",
        provider="test",
        price=Price(total=1000.0, currency="USD"),
        total_duration_minutes=1000,
        stops=len(layovers),
        segments=segments,
        layovers=layovers,
        transit_countries=transit_countries,
        risk=RiskAssessment(
            level=RiskLevel.LOW,
            reasons=[],
            verify_steps=[],
            transit_countries=[],
            layover_airports=[],
        ),
    )


def test_high_risk_overnight_layover():
    """Test that overnight layover triggers HIGH risk"""
    # Create segments with overnight layover
    seg1 = FlightSegment(
        carrier="AA",
        flight_number="AA100",
        from_airport="DEL",
        to_airport="DXB",
        depart_at="2026-02-10T22:00:00",
        arrive_at="2026-02-11T01:00:00",  # Next day
        duration_minutes=210,
    )
    seg2 = FlightSegment(
        carrier="AA",
        flight_number="AA101",
        from_airport="DXB",
        to_airport="JFK",
        depart_at="2026-02-11T08:00:00",  # 7 hours later, different day
        duration_minutes=840,
    )

    layover = Layover(airport="DXB", minutes=420, country="AE")
    itinerary = create_test_itinerary([layover], [seg1, seg2])

    risk = assess_risk(itinerary, "IN")

    assert risk.level == RiskLevel.HIGH
    assert any("OVERNIGHT" in reason for reason in risk.reasons)


def test_high_risk_long_layover():
    """Test that very long layover (>8h) triggers HIGH risk"""
    layover = Layover(airport="DXB", minutes=10 * 60, country="AE")  # 10 hours
    itinerary = create_test_itinerary([layover])

    risk = assess_risk(itinerary, "IN")

    assert risk.level == RiskLevel.HIGH
    assert any("long layover" in reason.lower() for reason in risk.reasons)


def test_high_risk_tight_connection():
    """Test that tight connection (<75 min) triggers HIGH risk"""
    layover = Layover(airport="DXB", minutes=60, country="AE")  # Only 60 minutes
    itinerary = create_test_itinerary([layover])

    risk = assess_risk(itinerary, "IN")

    assert risk.level == RiskLevel.HIGH
    assert any("TIGHT" in reason for reason in risk.reasons)


def test_high_risk_us_transit_without_visa():
    """Test that US transit without visa triggers HIGH risk"""
    layover = Layover(airport="JFK", minutes=180, country="US")
    itinerary = create_test_itinerary([layover])

    risk = assess_risk(itinerary, "IN")

    assert risk.level == RiskLevel.HIGH
    assert any("US" in reason for reason in risk.reasons)
    assert any("transit visa" in step.lower() for step in risk.verify_steps)


def test_medium_risk_us_transit_with_visa():
    """Test that US transit WITH visa reduces risk"""
    layover = Layover(airport="JFK", minutes=180, country="US")
    itinerary = create_test_itinerary([layover])

    travel_docs = TravelDocs(visas=["US"], residencies=[], notes="")
    risk = assess_risk(itinerary, "IN", travel_docs)

    # Should be reduced but still needs verification
    assert risk.level in [RiskLevel.MEDIUM, RiskLevel.LOW]
    assert any("US" in reason for reason in risk.reasons)


def test_medium_risk_schengen_transit():
    """Test that Schengen transit adds verification requirement"""
    layover = Layover(airport="FRA", minutes=180, country="DE")
    itinerary = create_test_itinerary([layover])

    risk = assess_risk(itinerary, "IN")

    assert risk.level == RiskLevel.MEDIUM
    assert any("Schengen" in reason for reason in risk.reasons)


def test_medium_risk_multiple_stops():
    """Test that multiple stops triggers MEDIUM risk"""
    layovers = [
        Layover(airport="DXB", minutes=120, country="AE"),
        Layover(airport="DOH", minutes=150, country="QA"),
    ]
    itinerary = create_test_itinerary(layovers)

    risk = assess_risk(itinerary, "IN")

    assert risk.level == RiskLevel.MEDIUM
    assert any("Multiple stops" in reason for reason in risk.reasons)


def test_preferred_transit_hub():
    """Test that preferred transit hubs can reduce risk"""
    # Singapore is a preferred hub
    layover = Layover(airport="SIN", minutes=150, country="SG")
    itinerary = create_test_itinerary([layover])

    risk = assess_risk(itinerary, "IN")

    # Should be LOW or MEDIUM (not HIGH)
    assert risk.level in [RiskLevel.LOW, RiskLevel.MEDIUM]


def test_default_verify_steps():
    """Test that default verify steps are always included"""
    layover = Layover(airport="DXB", minutes=120, country="AE")
    itinerary = create_test_itinerary([layover])

    risk = assess_risk(itinerary, "IN")

    default_steps = [
        "Confirm this is a single ticket",
        "Confirm baggage is checked through",
        "Verify you can remain airside",
    ]

    for expected in default_steps:
        assert any(expected in step for step in risk.verify_steps)
