"""Scraper Port — abstract interface for scraping data.

This module defines the contract that any scraping engine must implement to be used
by the application layer. By using the Ports and Adapters (Hexagonal) architecture,
the business logic remains decoupled from specific browser automation tools like
Playwright or Selenium.

The benefit of this abstract port is:
1. **Testability**: We can easily mock the scraper in unit tests.
2. **Flexibility**: We can swap Playwright for another technology without touching
    the core use cases.
3. **Decoupling**: The application layer only knows *what* it needs, not *how*
   it is achieved.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from src.application.dtos.scrape_request import ScrapeRequest
from src.domain.entities.place import Place


class ScraperPort(ABC):
    """Abstract base class defining the scraping interface.

    This port must be implemented by an infrastructure adapter.
    """

    @abstractmethod
    async def scrape(self, request: ScrapeRequest) -> AsyncIterator[Place]:
        """Asynchronously scrape Google Maps data based on the request.

        Args:
            request (ScrapeRequest): The validated input parameters for the search.

        Yields:
            AsyncIterator[Place]: An asynchronous iterator of Place entities
                extracted from the search results.

        Raises:
            Exception: Implementations may raise specific scrapers errors,
                which should be handled by the calling use case or entrypoint.
        """
        ...
