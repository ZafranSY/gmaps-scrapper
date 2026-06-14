"""Unit tests for the JsonPlaceRepository."""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime
from pathlib import Path

from src.infrastructure.repositories.json_repository import JsonPlaceRepository
from src.application.dtos.scrape_request import ScrapeRequest, ScrapeResult
from src.domain.entities.place import Place


def _make_result(places=None):
    """Create a minimal ScrapeResult for testing."""
    req = ScrapeRequest(keyword="nasi lemak", location="KL")
    result = ScrapeResult(
        request=req,
        started_at=datetime(2024, 6, 1, 12, 0, 0),
        finished_at=datetime(2024, 6, 1, 12, 0, 30),
    )
    if places:
        result.places = places
    return result


class TestJsonPlaceRepository:
    """Tests for the JsonPlaceRepository adapter."""

    def test_save_creates_file_at_output_path(self, tmp_path):
        out = tmp_path / "output.json"
        repo = JsonPlaceRepository(output_path=out)
        repo.save(_make_result([Place(name="Place A"), Place(name="Place B")]))
        assert out.exists()

    def test_saved_json_is_valid_json(self, tmp_path):
        out = tmp_path / "output.json"
        repo = JsonPlaceRepository(output_path=out)
        repo.save(_make_result([Place(name="Kedai Kopi")]))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_saved_json_has_metadata_key(self, tmp_path):
        out = tmp_path / "output.json"
        repo = JsonPlaceRepository(output_path=out)
        repo.save(_make_result([Place(name="Restoran")]))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "metadata" in data

    def test_saved_json_has_places_key(self, tmp_path):
        out = tmp_path / "output.json"
        repo = JsonPlaceRepository(output_path=out)
        repo.save(_make_result([Place(name="Warung")]))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "places" in data

    def test_saved_json_places_count_matches_result(self, tmp_path):
        out = tmp_path / "output.json"
        repo = JsonPlaceRepository(output_path=out)
        places = [Place(name="A"), Place(name="B")]
        repo.save(_make_result(places))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data["places"]) == 2

    def test_save_creates_parent_directories_if_missing(self, tmp_path):
        out = tmp_path / "subdir" / "nested" / "out.json"
        repo = JsonPlaceRepository(output_path=out)
        repo.save(_make_result([Place(name="Test")]))
        assert out.exists()

    def test_saved_json_uses_utf8(self, tmp_path):
        out = tmp_path / "output.json"
        repo = JsonPlaceRepository(output_path=out)
        repo.save(_make_result([Place(name="Warung Pak Mat ✓")]))
        content = out.read_text(encoding="utf-8")
        assert "Warung Pak Mat ✓" in content

    def test_saved_file_is_pretty_printed(self, tmp_path):
        out = tmp_path / "output.json"
        repo = JsonPlaceRepository(output_path=out)
        repo.save(_make_result([Place(name="Cafe")]))
        content = out.read_text(encoding="utf-8")
        assert "\n" in content  # Pretty printed has newlines
        assert "  " in content  # indent=2
