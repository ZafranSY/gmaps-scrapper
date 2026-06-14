"""Unit tests for value objects: Coordinates and OpeningHours."""
import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.domain.value_objects.coordinates import Coordinates
from src.domain.value_objects.opening_hours import OpeningHours


class TestCoordinates:
    """Tests for the Coordinates value object."""

    def test_valid_coordinates_created(self):
        c = Coordinates(lat=3.1390, lng=101.6869)
        assert c.lat == 3.1390
        assert c.lng == 101.6869

    def test_str_representation_is_lat_lng(self):
        c = Coordinates(lat=3.1390, lng=101.6869)
        assert str(c) == "3.139,101.6869"

    def test_lat_too_high_raises(self):
        with pytest.raises(ValueError):
            Coordinates(lat=91.0, lng=0.0)

    def test_lat_too_low_raises(self):
        with pytest.raises(ValueError):
            Coordinates(lat=-91.0, lng=0.0)

    def test_lng_too_high_raises(self):
        with pytest.raises(ValueError):
            Coordinates(lat=0.0, lng=181.0)

    def test_from_url_standard_google_maps_url(self):
        url = "https://www.google.com/maps/place/KLCC/@3.1577898,101.7119169,17z"
        c = Coordinates.from_url(url)
        assert c is not None
        assert abs(c.lat - 3.1577898) < 0.001
        assert abs(c.lng - 101.7119169) < 0.001

    def test_from_url_negative_coordinates(self):
        url = "https://www.google.com/maps/@-33.8688197,151.2092955,15z"
        c = Coordinates.from_url(url)
        assert c is not None
        assert c.lat < 0
        assert c.lng > 0

    def test_from_url_no_at_symbol_returns_none(self):
        url = "https://www.google.com/maps/place/SomePlace"
        c = Coordinates.from_url(url)
        assert c is None

    def test_frozen_model_raises_on_mutation(self):
        c = Coordinates(lat=3.0, lng=101.0)
        with pytest.raises(Exception):
            c.lat = 5.0


class TestOpeningHours:
    """Tests for the OpeningHours value object."""

    def test_from_dict_full_week_all_populated(self):
        raw = {
            "monday": "9 AM – 5 PM", "tuesday": "9 AM – 5 PM",
            "wednesday": "9 AM – 5 PM", "thursday": "9 AM – 5 PM",
            "friday": "9 AM – 5 PM", "saturday": "10 AM – 2 PM",
            "sunday": "Closed"
        }
        oh = OpeningHours.from_dict(raw)
        assert oh.monday == "9 AM – 5 PM"
        assert oh.sunday == "Closed"

    def test_from_dict_partial_week_missing_days_are_none(self):
        raw = {"monday": "9 AM – 5 PM", "friday": "9 AM – 3 PM"}
        oh = OpeningHours.from_dict(raw)
        assert oh.monday == "9 AM – 5 PM"
        assert oh.tuesday is None
        assert oh.friday == "9 AM – 3 PM"

    def test_from_dict_ignores_unknown_keys(self):
        raw = {"monday": "9 AM – 5 PM", "holiday": "Closed", "xyz": "test"}
        oh = OpeningHours.from_dict(raw)
        assert oh.monday == "9 AM – 5 PM"
        assert not hasattr(oh, "holiday")

    def test_to_dict_returns_all_seven_days(self):
        oh = OpeningHours.from_dict({"monday": "9 AM – 5 PM"})
        d = oh.to_dict()
        assert len(d) == 7
        assert "monday" in d
        assert "sunday" in d

    def test_immutability(self):
        oh = OpeningHours.from_dict({"monday": "9 AM – 5 PM"})
        with pytest.raises(Exception):
            oh.monday = "10 AM – 6 PM"
