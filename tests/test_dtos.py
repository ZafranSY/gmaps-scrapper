"""Unit tests for ScrapeRequest and ScrapeResult DTOs."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime
from pathlib import Path

from src.application.dtos.scrape_request import ScrapeRequest, ScrapeResult
from src.domain.entities.place import Place


class TestScrapeRequest:
    """Tests for the ScrapeRequest DTO."""

    def test_defaults_applied_for_limit_and_output(self):
        r = ScrapeRequest(keyword="nasi lemak", location="KL")
        assert r.limit == 200
        assert r.output_path == Path("results.json")

    def test_query_property_combines_keyword_and_location(self):
        r = ScrapeRequest(keyword="nasi lemak", location="Kuala Lumpur")
        assert r.query == "nasi lemak Kuala Lumpur"

    def test_limit_over_1000_is_capped_to_1000(self):
        r = ScrapeRequest(keyword="coffee", location="Penang", limit=2000)
        assert r.limit == 1000

    def test_empty_keyword_raises(self):
        with pytest.raises(ValueError):
            ScrapeRequest(keyword="", location="KL")

    def test_whitespace_keyword_raises(self):
        with pytest.raises(ValueError):
            ScrapeRequest(keyword="   ", location="KL")

    def test_empty_location_raises(self):
        with pytest.raises(ValueError):
            ScrapeRequest(keyword="food", location="")


class TestScrapeResult:
    """Tests for the ScrapeResult DTO."""

    def _make_request(self):
        return ScrapeRequest(keyword="test", location="test")

    def test_initial_total_collected_is_zero(self):
        result = ScrapeResult(request=self._make_request(), started_at=datetime(2024, 6, 1, 12, 0, 0))
        assert result.total_collected == 0

    def test_total_collected_matches_places_length(self):
        result = ScrapeResult(request=self._make_request(), started_at=datetime(2024, 6, 1, 12, 0, 0))
        result.places.append(Place(name="Place A"))
        result.places.append(Place(name="Place B"))
        assert result.total_collected == 2

    def test_duration_none_when_finished_at_not_set(self):
        result = ScrapeResult(request=self._make_request(), started_at=datetime(2024, 6, 1, 12, 0, 0))
        assert result.duration_seconds is None

    def test_duration_calculated_correctly(self):
        result = ScrapeResult(
            request=self._make_request(),
            started_at=datetime(2024, 6, 1, 12, 0, 0),
            finished_at=datetime(2024, 6, 1, 12, 0, 30)
        )
        assert result.duration_seconds == pytest.approx(30.0)

    def test_to_export_dict_has_metadata_and_places_keys(self):
        result = ScrapeResult(
            request=self._make_request(),
            started_at=datetime(2024, 6, 1, 12, 0, 0)
        )
        d = result.to_export_dict()
        assert "metadata" in d
        assert "places" in d

    def test_to_export_dict_metadata_has_correct_values(self):
        req = ScrapeRequest(keyword="coffee", location="Penang", limit=50)
        result = ScrapeResult(request=req, started_at=datetime(2024, 6, 1, 12, 0, 0))
        d = result.to_export_dict()
        assert d["metadata"]["keyword"] == "coffee"
        assert d["metadata"]["location"] == "Penang"
        assert d["metadata"]["limit"] == 50

    def test_to_export_dict_places_is_a_list(self):
        result = ScrapeResult(request=self._make_request(), started_at=datetime(2024, 6, 1, 12, 0, 0))
        d = result.to_export_dict()
        assert isinstance(d["places"], list)
