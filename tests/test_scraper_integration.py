"""Integration tests for PlaywrightGoogleMapsScraper using mocks.

These tests verify the scraper's internal logic (CAPTCHA detection,
stale-element scrolling, field extraction) WITHOUT launching a real browser.
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from src.infrastructure.scraping.playwright_scraper import PlaywrightGoogleMapsScraper


# ─── Helper to run async tests ───────────────────────────────────────────────


def run_async(coro):
    """Run an async coroutine synchronously for tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ─── CAPTCHA Detection ───────────────────────────────────────────────────────


class TestCaptchaDetection:
    """Tests for _check_for_captcha using mocked Page objects."""

    def _make_scraper(self):
        return PlaywrightGoogleMapsScraper(headless=True, verbose=False)

    def test_captcha_detected_via_url_sorry_index(self):
        scraper = self._make_scraper()
        page = MagicMock()
        page.url = "https://www.google.com/sorry/index?continue=https://www.google.com/maps"
        page.locator = MagicMock(return_value=MagicMock(count=AsyncMock(return_value=0)))

        result = run_async(scraper._check_for_captcha(page))
        assert result is True

    def test_captcha_detected_via_url_google_sorry(self):
        scraper = self._make_scraper()
        page = MagicMock()
        page.url = "https://google.com/sorry?q=something"
        page.locator = MagicMock(return_value=MagicMock(count=AsyncMock(return_value=0)))

        result = run_async(scraper._check_for_captcha(page))
        assert result is True

    def test_captcha_detected_via_dom_element(self):
        scraper = self._make_scraper()
        page = MagicMock()
        page.url = "https://www.google.com/maps"
        page.locator = MagicMock(return_value=MagicMock(count=AsyncMock(return_value=1)))

        result = run_async(scraper._check_for_captcha(page))
        assert result is True

    def test_no_captcha_on_normal_maps_page(self):
        scraper = self._make_scraper()
        page = MagicMock()
        page.url = "https://www.google.com/maps/search/nasi+lemak+KL"
        page.locator = MagicMock(return_value=MagicMock(count=AsyncMock(return_value=0)))

        result = run_async(scraper._check_for_captcha(page))
        assert result is False


# ─── No Results Detection ────────────────────────────────────────────────────


class TestNoResultsDetection:
    """Tests for _has_results using mocked Page objects."""

    def _make_scraper(self):
        return PlaywrightGoogleMapsScraper(headless=True, verbose=False)

    def test_has_results_returns_true_when_feed_found(self):
        scraper = self._make_scraper()
        page = AsyncMock()
        page.wait_for_selector = AsyncMock(return_value=True)

        result = run_async(scraper._has_results(page))
        assert result is True

    def test_has_results_returns_false_when_cant_find_message(self):
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        scraper = self._make_scraper()
        page = AsyncMock()
        page.wait_for_selector = AsyncMock(side_effect=PlaywrightTimeoutError("timeout"))
        page.content = AsyncMock(return_value="<html>Google Maps can't find some place</html>")

        result = run_async(scraper._has_results(page))
        assert result is False


# ─── Stale-Element Scrolling ─────────────────────────────────────────────────


class TestStaleScrolling:
    """Tests for _scroll_results stale-detection breakout."""

    def _make_scraper(self):
        return PlaywrightGoogleMapsScraper(headless=True, verbose=False)

    def test_scroll_breaks_after_3_stale_iterations(self):
        """Simulates cards that never grow — stale count should trigger exit."""
        scraper = self._make_scraper()
        page = AsyncMock()

        # Create 5 mock cards that stay at 5 forever
        mock_cards = [MagicMock() for _ in range(5)]
        for card in mock_cards:
            card.scroll_into_view_if_needed = AsyncMock()

        mock_locator = MagicMock()
        mock_locator.all = AsyncMock(return_value=mock_cards)
        page.locator = MagicMock(return_value=mock_locator)

        result = run_async(scraper._scroll_results(page, limit=20))

        # Should return the 5 available cards, not hang forever
        assert len(result) == 5

    def test_scroll_respects_limit(self):
        """When cards exceed the limit, truncate to limit."""
        scraper = self._make_scraper()
        page = AsyncMock()

        mock_cards = [MagicMock() for _ in range(10)]
        for card in mock_cards:
            card.scroll_into_view_if_needed = AsyncMock()

        mock_locator = MagicMock()
        mock_locator.all = AsyncMock(return_value=mock_cards)
        page.locator = MagicMock(return_value=mock_locator)

        result = run_async(scraper._scroll_results(page, limit=3))
        assert len(result) == 3


# ─── Field Extraction (Unit-level mocks) ─────────────────────────────────────


class TestFieldExtractors:
    """Tests for individual _extract_* methods with mocked DOM elements."""

    def _make_scraper(self):
        return PlaywrightGoogleMapsScraper(headless=True, verbose=False)

    def test_extract_rating_valid_decimal(self):
        scraper = self._make_scraper()
        page = MagicMock()
        mock_locator = MagicMock()
        mock_locator.first = MagicMock()
        mock_locator.first.inner_text = AsyncMock(return_value="4.5")
        page.locator = MagicMock(return_value=mock_locator)

        result = run_async(scraper._extract_rating(page))
        assert result == pytest.approx(4.5)

    def test_extract_rating_european_comma(self):
        scraper = self._make_scraper()
        page = MagicMock()
        mock_locator = MagicMock()
        mock_locator.first = MagicMock()
        mock_locator.first.inner_text = AsyncMock(return_value="4,7")
        page.locator = MagicMock(return_value=mock_locator)

        result = run_async(scraper._extract_rating(page))
        assert result == pytest.approx(4.7)

    def test_extract_rating_returns_none_when_text_empty(self):
        scraper = self._make_scraper()
        page = MagicMock()
        mock_locator = MagicMock()
        mock_locator.first = MagicMock()
        mock_locator.first.inner_text = AsyncMock(return_value="")
        page.locator = MagicMock(return_value=mock_locator)

        result = run_async(scraper._extract_rating(page))
        assert result is None

    def test_extract_reviews_count_standard(self):
        scraper = self._make_scraper()
        page = MagicMock()
        mock_locator = MagicMock()
        mock_locator.first = MagicMock()
        mock_locator.first.get_attribute = AsyncMock(return_value="1,234 reviews")
        page.locator = MagicMock(return_value=mock_locator)

        result = run_async(scraper._extract_reviews_count(page))
        assert result == 1234

    def test_extract_reviews_count_k_suffix(self):
        scraper = self._make_scraper()
        page = MagicMock()
        mock_locator = MagicMock()
        mock_locator.first = MagicMock()
        mock_locator.first.get_attribute = AsyncMock(return_value="2.3K reviews")
        page.locator = MagicMock(return_value=mock_locator)

        result = run_async(scraper._extract_reviews_count(page))
        assert result == 2300

    def test_extract_website_returns_href(self):
        scraper = self._make_scraper()
        page = MagicMock()
        mock_locator = MagicMock()
        mock_locator.first = MagicMock()
        mock_locator.first.get_attribute = AsyncMock(return_value="https://example.com")
        page.locator = MagicMock(return_value=mock_locator)

        result = run_async(scraper._extract_website(page))
        assert result == "https://example.com"

    def test_extract_phone_from_data_item_id(self):
        scraper = self._make_scraper()
        page = MagicMock()
        mock_locator = MagicMock()
        mock_locator.first = MagicMock()
        mock_locator.first.get_attribute = AsyncMock(return_value="phone:tel:+60312345678")
        page.locator = MagicMock(return_value=mock_locator)

        result = run_async(scraper._extract_phone(page))
        assert "+60312345678" in result

    def test_extract_place_id_from_url(self):
        url = "https://www.google.com/maps/place/Test/data=!4m5!3m4!1s0x0:0x0!8m2!3d3.1!4d101.7?entry=ttu&g_ep=ChIJN1t_tDeuEmsRUsoyG83frY4"
        result = PlaywrightGoogleMapsScraper._extract_place_id(url)
        assert result is not None
        assert result.startswith("ChIJ")

    def test_extract_place_id_missing_returns_none(self):
        url = "https://www.google.com/maps/search/nasi+lemak"
        result = PlaywrightGoogleMapsScraper._extract_place_id(url)
        assert result is None


# ─── Coordinates Parsing ─────────────────────────────────────────────────────


class TestCoordinatesParsing:
    """Tests for _parse_coordinates from URL."""

    def _make_scraper(self):
        return PlaywrightGoogleMapsScraper(headless=True, verbose=False)

    def test_parse_coordinates_from_standard_url(self):
        scraper = self._make_scraper()
        url = "https://www.google.com/maps/place/KLCC/@3.1577898,101.7119169,17z"
        result = run_async(scraper._parse_coordinates(url))
        assert result is not None
        assert abs(result.lat - 3.1577898) < 0.001
        assert abs(result.lng - 101.7119169) < 0.001

    def test_parse_coordinates_returns_none_for_bad_url(self):
        scraper = self._make_scraper()
        url = "https://www.google.com/maps/search/nasi+lemak"
        result = run_async(scraper._parse_coordinates(url))
        assert result is None
