"""Playwright Scraper — infrastructure adapter for Google Maps.

This module implements the ScraperPort using Playwright browser automation.
It focuses on navigating the Google Maps DOM, scrolling results, and extracting 
structured data from the sidebars.
"""
from __future__ import annotations

import asyncio
import logging
import random
import re
from datetime import datetime
from typing import AsyncIterator, List, Optional

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Locator, Page, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.application.dtos.scrape_request import ScrapeRequest
from src.application.ports.scraper_port import ScraperPort
from src.domain.entities.place import Place
from src.domain.value_objects.coordinates import Coordinates
from src.domain.value_objects.opening_hours import OpeningHours

# Configure logging for the scraper
logger = logging.getLogger(__name__)

# --- SELECTOR CONSTANTS ---
RESULTS_PANE_SELECTOR = 'div[role="feed"]'
RESULT_CARD_SELECTOR = 'a.hfpxzc'
# Fallback for result cards if a.hfpxzc fails
RESULT_CARD_FALLBACK = 'div[role="feed"] > div > div[jsaction]'
SIDEBAR_NAME_SELECTOR = 'h1.DUwDvf'
SIDEBAR_CATEGORY_SELECTOR = 'button.DkEaL'
SIDEBAR_RATING_SELECTOR = 'span.MW4etd'
SIDEBAR_REVIEWS_SELECTOR = 'span.ZkP5Je, span[aria-label*="review"], span.UY7F9'
SIDEBAR_ADDRESS_SELECTOR = 'button[data-item-id="address"]'
SIDEBAR_PHONE_SELECTOR = 'button[data-item-id^="phone"]'
SIDEBAR_WEBSITE_SELECTOR = 'a[data-item-id="authority"]'
SIDEBAR_HOURS_TABLE_SELECTOR = 'table.eK4R0e'
SEARCH_BOX_SELECTOR = 'input[name="q"]'
SIDEBAR_PLUS_CODE_SELECTOR = 'button[data-item-id="oloc"]'

# --- CONFIGURATION CONSTANTS ---
DEFAULT_TIMEOUT = 8000
CARD_TIMEOUT = 5000
SCROLL_PAUSE_MS = 1500
MAX_CLICK_RETRIES = 2


class PlaywrightGoogleMapsScraper(ScraperPort):
    """Scraper implementation using Playwright."""

    def __init__(self, headless: bool = False, verbose: bool = False) -> None:
        """Initialise with browser settings.

        Args:
            headless (bool): Whether to run the browser without a GUI.
            verbose (bool): Whether to enable detailed debug logging.
        """
        self.headless = headless
        self.verbose = verbose

    async def scrape(self, request: ScrapeRequest) -> AsyncIterator[Place]:
        """Asynchronously scrape Google Maps data based on the request.

        This is the main entry point for the scraping session. It orchestrates
        the browser launch, search, scrolling, and card extraction.

        Args:
            request (ScrapeRequest): The validated input parameters for the search.

        Yields:
            AsyncIterator[Place]: An asynchronous iterator of Place entities
                extracted from the search results.
        """
        async with async_playwright() as pw:
            # Launch chromium with anti-bot arguments
            browser = await pw.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )
            
            # Create isolated context with realistic viewport and user agent
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US"
            )
            
            page = await context.new_page()
            
            try:
                # 1. Step into Google Maps
                await self._open_maps(page)
                
                # 2. Submit the search query
                await self._search(page, request.query)
                
                # 2.5 CAPTCHA check — bail early if Google is blocking
                if await self._check_for_captcha(page):
                    return
                
                # 2.6 No-results check
                if not await self._has_results(page):
                    logger.warning("No results found for query: %s", request.query)
                    print(f"⚠️  No results found for \"{request.query}\"", flush=True)
                    return
                
                # 3. Wait for cards to stabilize after search
                await self._random_sleep(2, 4)
                
                # 4. Scroll result pane to load enough cards
                cards = await self._scroll_results(page, request.limit)
                logger.info("Collected %d visible cards", len(cards))
                
                # 5. Extract data from each card
                count = 0
                for card in cards:
                    if request.limit > 0 and count >= request.limit:
                        break
                        
                    # Detailed extraction (sidebar click + collection)
                    place = await self._extract_place(page, card)
                    
                    if place is not None:
                        count += 1
                        yield place
                        
                    # Random pause between extractions to avoid bot detection
                    await self._random_sleep(2, 6)
                
            finally:
                # Ensure browser resources are always cleaned up
                await context.close()
                await browser.close()

    # --- PRIVATE METHODS ---

    async def _check_for_captcha(self, page: Page) -> bool:
        """Detect if Google has presented a CAPTCHA challenge.

        Checks the URL for redirect patterns and the DOM for CAPTCHA elements.

        Args:
            page (Page): The active Playwright page.

        Returns:
            bool: True if CAPTCHA is detected.
        """
        current_url = page.url
        
        # Check URL-based redirect
        if "sorry/index" in current_url or "google.com/sorry" in current_url:
            logger.error("CAPTCHA detected (URL redirect). Stopping scrape.")
            print("🚫 CAPTCHA detected. Google is blocking requests. Stopping scrape.", flush=True)
            return True
        
        # Check DOM for captcha element
        try:
            captcha_count = await page.locator("#captcha").count()
            if captcha_count > 0:
                logger.error("CAPTCHA detected (DOM element). Stopping scrape.")
                print("🚫 CAPTCHA detected. Google is blocking requests. Stopping scrape.", flush=True)
                return True
        except Exception:
            pass
        
        return False

    async def _has_results(self, page: Page) -> bool:
        """Check if the search returned any results.

        Waits for the results pane to appear. If it does not, checks
        whether Google displayed a 'can't find' message.

        Args:
            page (Page): The active Playwright page.

        Returns:
            bool: True if there are results visible.
        """
        try:
            # Wait longer for results pane (10s)
            await page.wait_for_selector(RESULTS_PANE_SELECTOR, timeout=10000)
            
            # Additional check: ensure at least one card or fallback is present
            # We give it a moment to load the first few cards
            for _ in range(3):
                cards = await page.locator(RESULT_CARD_SELECTOR).all()
                if len(cards) > 0:
                    return True
                fallback_cards = await page.locator(RESULT_CARD_FALLBACK).all()
                if len(fallback_cards) > 0:
                    return True
                await asyncio.sleep(1)
                
            return False
        except PlaywrightTimeoutError:
            # Check if the page shows a specific "no results" message
            try:
                content = await page.content()
                if "Google Maps can't find" in content or "No results found" in content:
                    return False
            except Exception:
                pass
            return False

    async def _open_maps(self, page: Page) -> None:
        """Navigate to Google Maps and handle initial setup.

        Handles cookie consent prompts and waits for the search box to be ready.

        Args:
            page (Page): The active Playwright page.

        Raises:
            PlaywrightTimeoutError: If Google Maps or the search box fails to load.
        """
        logger.debug("Navigating to https://www.google.com/maps")
        await page.goto("https://www.google.com/maps", timeout=30000)
        
        # Handle cookie consent if it appears
        try:
            # Look for common "Accept all" button labels in English
            consent_btn = page.get_by_role("button", name="Accept all")
            await consent_btn.click(timeout=4000)
            logger.debug("Cookie consent accepted.")
        except PlaywrightTimeoutError:
            logger.debug("Cookie consent button not found or already accepted.")

        # Wait for the main UI element to verify we are on the right page
        await page.wait_for_selector(SEARCH_BOX_SELECTOR, timeout=15000)
        logger.debug("Google Maps search box is ready.")

    async def _search(self, page: Page, query: str) -> None:
        """Submit a search query to the Google Maps search box.

        This method mimics human typing by adding random delays between
        keystrokes and pauses between actions.

        Args:
            page (Page): The active Playwright page.
            query (str): The search keyword and location.
        """
        logger.debug("Submitting search query: %s", query)
        
        # Locate the search box and focus it
        search_box = page.locator(SEARCH_BOX_SELECTOR)
        await search_box.click()
        await self._random_sleep(0.5, 1.5)
        
        # Mimic human typing
        for char in query:
            await page.keyboard.type(char, delay=random.randint(50, 120))
            
        await self._random_sleep(0.5, 1.0)
        
        # Submit the search
        await page.keyboard.press("Enter")
        
        # Wait for the results pane to appear
        try:
            await page.wait_for_selector(RESULTS_PANE_SELECTOR, timeout=15000)
            logger.debug("Results pane appeared.")
        except PlaywrightTimeoutError:
            logger.warning(
                "Results pane did not appear — "
                "this might be a single result or no results found."
            )

    async def _scroll_results(self, page: Page, limit: int) -> List[Locator]:
        """Scroll the results pane until the limit or bottom is reached.

        This method uses a stale-detection strategy: it scrolls the last card
        into view and checks if the count of results increases. If the count
        does not change after multiple attempts, we assume we reached the end.

        Args:
            page (Page): The active Playwright page.
            limit (int): The maximum number of cards to collect.

        Returns:
            List[Locator]: A list of Playwright locators for result cards.
        """
        logger.debug("Starting results scrolling (limit: %d)", limit)
        
        previous_count = 0
        print(f"Starting results scrolling (limit: {'unlimited' if limit <= 0 else limit})")
        stale_count = 0
        
        while True:
            # Try primary selector first, then fallback
            cards = await page.locator(RESULT_CARD_SELECTOR).all()
            if not cards:
                cards = await page.locator(RESULT_CARD_FALLBACK).all()
                
            current_count = len(cards)
            logger.debug("Current visible cards: %d", current_count)
            
            # Check if we have enough results (only if limit > 0)
            if limit > 0 and current_count >= limit:
                print(f"Limit reached ({current_count}/{limit})")
                break
                
            # Check for stale results (reached the bottom)
            if current_count == previous_count:
                stale_count += 1
                # If we have 0 results, be more patient (5 attempts)
                limit_stale = 5 if current_count == 0 else 3
                if stale_count >= limit_stale:
                    logger.debug("Reached bottom of results (stale_count=%d)", stale_count)
                    break
            else:
                stale_count = 0
                
            previous_count = current_count
            
            # Scroll to trigger lazy loading
            try:
                if cards:
                    # Scroll last card into view
                    await cards[-1].scroll_into_view_if_needed(timeout=3000)
                else:
                    # Fallback if no cards are visible yet — scroll the pane itself
                    await page.locator(RESULTS_PANE_SELECTOR).evaluate("el => el.scrollBy(0, 1000)")
            except (PlaywrightError, Exception):
                # Fallback to manual scrolling if JS-based scroll fails
                try:
                    await page.locator(RESULTS_PANE_SELECTOR).evaluate("el => el.scrollBy(0, 1000)")
                except Exception:
                    pass
                
            # Pause to allow for network load
            await asyncio.sleep(SCROLL_PAUSE_MS / 1000.0)
            
        # Collect final set of cards and truncate to limit
        all_cards = await page.locator(RESULT_CARD_SELECTOR).all()
        if not all_cards:
            all_cards = await page.locator(RESULT_CARD_FALLBACK).all()
            
        if limit > 0:
            final_list = all_cards[:limit]
        else:
            final_list = all_cards
        
        logger.info("Final collection: %d visible cards", len(final_list))
        return final_list

    async def _extract_place(self, page: Page, card: Locator) -> Optional[Place]:
        """Click a result card and extract detailed information from the sidebar.

        This method coordinates the sidebar interaction and delegates field-level
        extraction to specialized private methods.

        Args:
            page (Page): The active Playwright page.
            card (Locator): The locator for the specific result card.

        Returns:
            Optional[Place]: A populated Place entity or None if extraction fails.
        """
        # Click with retry — Google Maps cards sometimes miss the first click
        for attempt in range(1, MAX_CLICK_RETRIES + 1):
            try:
                await card.click(timeout=CARD_TIMEOUT)
                await page.wait_for_selector(SIDEBAR_NAME_SELECTOR, timeout=DEFAULT_TIMEOUT)
                break  # Success
            except (PlaywrightTimeoutError, Exception) as exc:
                if attempt < MAX_CLICK_RETRIES:
                    logger.debug("Card click attempt %d failed, retrying...", attempt)
                    await asyncio.sleep(1.5)
                else:
                    logger.warning("Card click failed after %d attempts: %s", attempt, exc)
                    return None

        # Extract fields using specialized methods
        name = await self._safe_text(page, SIDEBAR_NAME_SELECTOR)
        if not name:
            logger.warning("Could not extract place name from sidebar.")
            return None
            
        category = await self._safe_text(page, SIDEBAR_CATEGORY_SELECTOR)
        rating = await self._extract_rating(page)
        reviews_count = await self._extract_reviews_count(page)
        price_level = await self._extract_price_level(page)
        address = await self._safe_text(page, SIDEBAR_ADDRESS_SELECTOR)
        phone = await self._extract_phone(page)
        website = await self._extract_website(page)
        website_classification = self._classify_website(website)
        opening_hours = await self._extract_hours(page)
        
        # Parse dynamic data from the current URL
        current_url = page.url
        coordinates = await self._parse_coordinates(current_url)
        place_id = self._extract_place_id(current_url)
        
        photos_urls = await self._extract_photos(page)
        plus_code = await self._safe_text(page, SIDEBAR_PLUS_CODE_SELECTOR)
        
        self._debug(f"Extracted: {name!r} | rating={rating}")
        
        # Construct and return the core entity
        return Place(
            place_id=place_id or "",
            name=name,
            category=category,
            rating=rating,
            reviews_count=reviews_count,
            price_level=price_level,
            address=address,
            phone=phone,
            website=website,
            website_classification=website_classification,
            opening_hours=opening_hours,
            coordinates=coordinates,
            photos_urls=photos_urls,
            plus_code=plus_code,
            scraped_at=datetime.utcnow()
        )

    async def _extract_rating(self, page: Page) -> Optional[float]:
        """Extract the numeric rating from the sidebar.

        Reads the text value (e.g., "4.5"), handles European decimal commas,
        and converts to float.

        Args:
            page (Page): The active Playwright page.

        Returns:
            Optional[float]: The rating value or None if not found/invalid.
        """
        raw_text = await self._safe_text(page, SIDEBAR_RATING_SELECTOR)
        if not raw_text:
            return None
            
        try:
            # Handle both "4.5" and "4,5" formats
            clean_text = raw_text.replace(",", ".")
            return float(clean_text)
        except (ValueError, TypeError):
            return None

    async def _extract_reviews_count(self, page: Page) -> Optional[int]:
        """Extract the total number of reviews from the sidebar.

        Parses the aria-label attribute which often contains text like
        "1,234 reviews" or "2.3K reviews", or extracts directly from text.

        Args:
            page (Page): The active Playwright page.

        Returns:
            Optional[int]: The total reviews count or None if not found.
        """
        try:
            # Try to get from aria-label first (usually more detailed)
            locator = page.locator(SIDEBAR_REVIEWS_SELECTOR).first
            label = await locator.get_attribute("aria-label", timeout=CARD_TIMEOUT)
            
            if label:
                # Regex to extract the numeric part from "X reviews" or "X stars Y reviews"
                match = re.search(r"([\d,\.]+)[Kk]?\s*review", label, re.IGNORECASE)
                if match:
                    raw_num = match.group(1).replace(",", "")
                    num = float(raw_num)
                    if "K" in match.group(0).upper():
                        num *= 1000
                    return int(num)

            # Fallback: try inner text from a specific span like UY7F9
            text = await self._safe_text(page, "span.UY7F9")
            if text:
                # Remove parentheses and other non-numeric chars
                clean_text = re.sub(r"[^\d]", "", text)
                if clean_text:
                    return int(clean_text)
                    
            return None
        except Exception:
            return None

    async def _extract_price_level(self, page: Page) -> Optional[str]:
        """Extract the price level indicator (e.g., "$$") from the sidebar.

        Reads the aria-label of the price span and uses regex to find
        the currency symbols.

        Args:
            page (Page): The active Playwright page.

        Returns:
            Optional[str]: The price level (e.g., "$$") or None.
        """
        try:
            selector = 'span.mgr77e > span[aria-label*="Price"]'
            locator = page.locator(selector).first
            label = await locator.get_attribute("aria-label", timeout=CARD_TIMEOUT)
            
            if not label:
                return None
                
            match = re.search(r"Price:\s*(\$+)", label)
            return match.group(1) if match else None
        except Exception:
            return None

    def _classify_website(self, url: Optional[str]) -> Optional[str]:
        """Classify a website URL into outreach signals.

        Args:
            url (Optional[str]): The website URL.

        Returns:
            Optional[str]: The signal type ('linktree', 'whatsapp', 'facebook') or None.
        """
        if not url:
            return None
            
        lowered = url.lower()
        if "linktr.ee" in lowered or "linktree" in lowered:
            return "linktree"
        if "wa.me" in lowered or "whatsapp.com" in lowered:
            return "whatsapp"
        if "facebook.com" in lowered or "fb.com" in lowered:
            return "facebook"
        if "instagram.com" in lowered or "ig.me" in lowered:
            return "instagram"
            
        return None

    async def _extract_phone(self, page: Page) -> Optional[str]:
        """Extract the formatted phone number from the sidebar.

        Prefers the data-item-id attribute with the 'tel:' prefix, 
        falling back to the aria-label if necessary.

        Args:
            page (Page): The active Playwright page.

        Returns:
            Optional[str]: The phone number or None.
        """
        try:
            locator = page.locator(SIDEBAR_PHONE_SELECTOR).first
            
            # Primary: Extract from data-item-id (cleanest format)
            item_id = await locator.get_attribute("data-item-id", timeout=CARD_TIMEOUT)
            if item_id:
                match = re.search(r"tel:(.+)", item_id)
                if match:
                    return match.group(1)
                    
            # Fallback: Extract from aria-label
            label = await locator.get_attribute("aria-label", timeout=CARD_TIMEOUT)
            if label:
                return label.replace("Phone:", "").strip()
                
            return None
        except Exception:
            return None

    async def _extract_website(self, page: Page) -> Optional[str]:
        """Extract the official website URL from the sidebar.

        Reads the href attribute from the authority link.

        Args:
            page (Page): The active Playwright page.

        Returns:
            Optional[str]: The website URL or None.
        """
        try:
            locator = page.locator(SIDEBAR_WEBSITE_SELECTOR).first
            return await locator.get_attribute("href", timeout=CARD_TIMEOUT)
        except Exception:
            return None

    async def _extract_hours(self, page: Page) -> Optional[OpeningHours]:
        """Extract the weekly opening hours from the sidebar.

        Triggers a click on the expansion button to reveal the full table,
        then parses each row for day-to-hours mapping.

        Args:
            page (Page): The active Playwright page.

        Returns:
            Optional[OpeningHours]: A populated hours object or None.
        """
        day_map = {
            "mon": "monday", "tue": "tuesday", "wed": "wednesday",
            "thu": "thursday", "fri": "friday", "sat": "saturday", "sun": "sunday"
        }
        
        try:
            # 1. Expand the hours table
            expand_btn = page.locator('button[data-item-id="oh"]').first
            await expand_btn.click(timeout=3000)
            await asyncio.sleep(0.8) # Wait for expansion animation
            
            # 2. Wait for the table to appear
            table = page.locator(SIDEBAR_HOURS_TABLE_SELECTOR).first
            await table.wait_for(state="visible", timeout=3000)
            
            # 3. Read rows
            rows = await table.locator("tr").all()
            hours_dict = {}
            
            for row in rows:
                cells = await row.locator("td").all()
                if len(cells) >= 2:
                    day_text = (await cells[0].inner_text()).strip().lower().rstrip(":")
                    hours_text = (await cells[1].inner_text()).strip()
                    
                    # Normalize day names (handle abbreviations)
                    normalized_day = day_text
                    for abbrev, full in day_map.items():
                        if day_text.startswith(abbrev):
                            normalized_day = full
                            break
                    
                    if normalized_day in day_map.values():
                        hours_dict[normalized_day] = hours_text
            
            if hours_dict:
                return OpeningHours.from_dict(hours_dict)
            return None
        except Exception as exc:
            logger.debug("Failed to extract hours: %s", exc)
            return None

    async def _extract_photos(self, page: Page) -> List[str]:
        """Extract thumbnail URLs from the sidebar photo gallery.

        Limited to the first 5 images that appear in the hero header.

        Args:
            page (Page): The active Playwright page.

        Returns:
            List[str]: A list of absolute image URLs.
        """
        try:
            selector = 'button[jsaction*="pane.heroHeaderImage"] img'
            images = await page.locator(selector).all()
            
            urls = []
            for img in images[:5]:
                src = await img.get_attribute("src")
                if src and src.startswith("http"):
                    urls.append(src)
            return urls
        except Exception:
            return []

    async def _parse_coordinates(self, url: str) -> Optional[Coordinates]:
        """Parse coordinates from the current page URL.

        Delegates the regex parsing to the Coordinates value object.

        Args:
            url (str): The current Google Maps URL.

        Returns:
            Optional[Coordinates]: Populated coordinates or None.
        """
        try:
            return Coordinates.from_url(url)
        except Exception:
            return None

    @staticmethod
    def _extract_place_id(url: str) -> Optional[str]:
        """Extract the Google Place ID from the page URL.

        Google Place IDs in URLs typically start with 'ChIJ'.

        Args:
            url (str): The current Google Maps URL.

        Returns:
            Optional[str]: The Place ID or None.
        """
        match = re.search(r"(ChIJ[^!&?/\"]+)", url)
        return match.group(1) if match else None

    async def _safe_text(self, page: Page, selector: str) -> Optional[str]:
        """Safely extract stripped text from a selector.

        Wait for the selector to be present up to CARD_TIMEOUT and returns
        the inner text. Catch all exceptions to prevent extraction crashes.

        Args:
            page (Page): The active Playwright page.
            selector (str): The CSS selector to query.

        Returns:
            Optional[str]: Stripped text or None if selection fails.
        """
        try:
            locator = page.locator(selector).first
            text = await locator.inner_text(timeout=CARD_TIMEOUT)
            return text.strip() if text else None
        except Exception:
            # We intentionally catch all here to make individual field failures non-fatal
            return None

    async def _random_sleep(self, min_s: float = 2.0, max_s: float = 8.0) -> None:
        """Wait for a random duration to mimic human behaviour.

        Args:
            min_s (float): Minimum sleep time in seconds.
            max_s (float): Maximum sleep time in seconds.
        """
        duration = random.uniform(min_s, max_s)
        logger.debug("Sleeping %.1fs", duration)
        await asyncio.sleep(duration)

    def _debug(self, message: str) -> None:
        """Log a debug message if verbose mode is enabled.

        Args:
            message (str): The message to log.
        """
        if self.verbose:
            logger.debug(message)
