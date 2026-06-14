"""Unit tests for the Place entity."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.domain.entities.place import Place
from src.domain.value_objects.coordinates import Coordinates
from src.domain.value_objects.opening_hours import OpeningHours


class TestPlace:
    """Tests for the Place domain entity."""

    def test_minimal_place_with_name_only(self):
        p = Place(name="Nasi Lemak Antarabangsa")
        assert p.name == "Nasi Lemak Antarabangsa"

    def test_auto_place_id_is_non_empty_string(self):
        p = Place(name="Restoran Syed")
        assert isinstance(p.place_id, str)
        assert len(p.place_id) > 0

    def test_photos_urls_defaults_to_empty_list(self):
        p = Place(name="Warung Pak Mat")
        assert p.photos_urls == []

    def test_rating_4_5_accepted(self):
        p = Place(name="Kedai Kopi", rating=4.5)
        assert p.rating == 4.5

    @pytest.mark.parametrize("bad_rating", [5.1, 6.0, 10.0, -0.1, -1.0])
    def test_invalid_rating_raises(self, bad_rating):
        with pytest.raises(ValueError):
            Place(name="Test", rating=bad_rating)

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            Place(name="")

    def test_whitespace_only_name_raises(self):
        with pytest.raises(ValueError):
            Place(name="   ")

    def test_negative_reviews_count_raises(self):
        with pytest.raises(ValueError):
            Place(name="Test", reviews_count=-1)

    def test_to_export_dict_has_all_expected_keys(self):
        p = Place(name="Restoran Nasi Kandar", rating=4.2, reviews_count=500)
        d = p.to_export_dict()
        assert "name" in d
        assert "rating" in d
        assert "reviews_count" in d
        assert "scraped_at" in d

    def test_to_export_dict_scraped_at_is_iso_string(self):
        p = Place(name="Teh Tarik Corner")
        d = p.to_export_dict()
        assert isinstance(d["scraped_at"], str)
        assert "T" in d["scraped_at"]  # ISO format contains T separator

    def test_to_export_dict_coordinates_serialized_as_dict(self):
        coords = Coordinates(lat=3.139, lng=101.6869)
        p = Place(name="KLCC Food Court", coordinates=coords)
        d = p.to_export_dict()
        assert d["coordinates"] == {"lat": 3.139, "lng": 101.6869}

    def test_to_export_dict_opening_hours_serialized_as_dict(self):
        oh = OpeningHours.from_dict({"monday": "9 AM – 5 PM"})
        p = Place(name="Sunday Market", opening_hours=oh)
        d = p.to_export_dict()
        assert "monday" in d["opening_hours"]
        assert len(d["opening_hours"]) == 7

    def test_to_export_dict_none_coordinates_is_none(self):
        p = Place(name="No Coords Cafe")
        d = p.to_export_dict()
        assert d["coordinates"] is None

    def test_repr_contains_name_and_rating(self):
        p = Place(name="Mamak Stall", rating=4.0)
        r = repr(p)
        assert "Mamak Stall" in r
        assert "4.0" in r
