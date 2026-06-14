"""Shared pytest fixtures for gmaps-scraper tests."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime

from src.domain.value_objects.coordinates import Coordinates
from src.domain.value_objects.opening_hours import OpeningHours
from src.domain.entities.place import Place
from src.application.dtos.scrape_request import ScrapeRequest, ScrapeResult


@pytest.fixture
def sample_coordinates() -> Coordinates:
    """Kuala Lumpur city centre coordinates."""
    return Coordinates(lat=3.1390, lng=101.6869)


@pytest.fixture
def sample_opening_hours() -> OpeningHours:
    """Partial week opening hours fixture."""
    return OpeningHours.from_dict({
        "monday": "9 AM – 5 PM",
        "friday": "9 AM – 3 PM",
        "sunday": "Closed",
    })


@pytest.fixture
def sample_place(sample_coordinates, sample_opening_hours) -> Place:
    """A realistic Malaysian restaurant place fixture."""
    return Place(
        name="Nasi Lemak Antarabangsa",
        category="Malaysian restaurant",
        rating=4.5,
        reviews_count=2341,
        price_level="$$",
        address="Jalan Raja Muda Musa, Kampung Baru, KL",
        phone="+60 3-2692 8728",
        website="https://example.com",
        opening_hours=sample_opening_hours,
        coordinates=sample_coordinates,
        photos_urls=["https://lh5.googleusercontent.com/p/ABC123"],
        plus_code="6PM3+CH Kuala Lumpur",
    )


@pytest.fixture
def sample_request() -> ScrapeRequest:
    """Standard scrape request fixture."""
    return ScrapeRequest(
        keyword="nasi lemak",
        location="Kuala Lumpur, Malaysia",
        limit=10,
    )


@pytest.fixture
def sample_result(sample_request, sample_place) -> ScrapeResult:
    """A completed scrape result with one place."""
    result = ScrapeResult(
        request=sample_request,
        started_at=datetime(2024, 6, 1, 12, 0, 0),
        finished_at=datetime(2024, 6, 1, 12, 30, 0),
    )
    result.places.append(sample_place)
    return result
