"""Scrape Use Case — orchestrates the scrape and save flow.

This module provides the core business logic for the Google Maps scraping application.
It acts as a coordinator between the scraper port (data collection) and the
repository port (data persistence).
"""
from __future__ import annotations

import logging
from datetime import datetime

from src.application.dtos.scrape_request import ScrapeRequest, ScrapeResult
from src.application.ports.repository_port import RepositoryPort
from src.application.ports.scraper_port import ScraperPort
from src.domain.entities.place import Place

# Configure logging for the use case
logger = logging.getLogger(__name__)


class ScrapeUseCase:
    """Orchestrates the Google Maps collection workflow.

    The Use Case defines the cross-layer logic:
    1. Start a scraping session via the scraper.
    2. Collect and log progress of extracted places.
    3. Finalize and persist the session results via the repository.

    Args:
        scraper (ScraperPort): An implementation of the Scraper abstract port.
        repository (RepositoryPort): An implementation of the Repository abstract port.
    """

    def __init__(self, scraper: ScraperPort, repository: RepositoryPort):
        """Initialise the use case with inward-facing ports."""
        self._scraper = scraper
        self._repository = repository

    async def execute(self, request: ScrapeRequest) -> ScrapeResult:
        """Execute the full scraping and saving process.

        Starts the browser, scrolls and extracts place data, and ensures the
        results are saved even if partial failure occurs during iteration.
        If a mid-scrape error occurs with partial data, results are saved.
        If a mid-scrape error occurs with 0 data, the exception is re-raised.

        Args:
            request (ScrapeRequest): The validated input parameters for the scrape.

        Returns:
            ScrapeResult: The completed result containing collected place entities
                and session metadata.

        Raises:
            Exception: Re-raises if the scraper fails AND 0 places collected.
        """
        # Create result container with start time
        result = ScrapeResult(
            request=request, 
            started_at=datetime.utcnow()
        )
        
        scrape_error = None

        try:
            # Iterate through the asynchronous generator provided by the scraper
            async for place in self._scraper.scrape(request):
                result.places.append(place)
                
                # Log progress to terminal and logs
                self._log_progress(
                    place=place, 
                    count=result.total_collected, 
                    limit=request.limit
                )

                # Check if we have manually reached the requested limit
                # Only enforce when limit > 0 (0 means unlimited)
                if request.limit > 0 and result.total_collected >= request.limit:
                    logger.debug("Reached requested limit: %d", request.limit)
                    break

        except Exception as exc:
            scrape_error = exc
            logger.error(
                "Scraper error after %d places: %s",
                result.total_collected, exc
            )
                    
        finally:
            # Ensure finished_at is always set, even on error
            result.finished_at = datetime.utcnow()
            
            # Always save — even with 0 places (metadata is still useful)
            self._repository.save(result)
            logger.info("Saved %d places to repository.", result.total_collected)

        # Post-save error handling
        if scrape_error is not None:
            if result.total_collected > 0:
                logger.warning(
                    "Partial results saved (%d places). Original error: %s",
                    result.total_collected, scrape_error
                )
                print(
                    f"⚠️  Scrape interrupted after {result.total_collected} places. "
                    "Partial results were saved.", flush=True
                )
            else:
                # No data collected — re-raise to signal total failure
                raise scrape_error
        
        return result


    def _log_progress(self, place: Place, count: int, limit: int) -> None:
        """Log a summary of the current scraping progress.

        Outputs to both the standard logger (INFO) and user-facing STDOUT.

        Args:
            place (Place): The most recently collected place entity.
            count (int): Current total count of places collected.
            limit (int): The target limit for the scrape session.
        """
        status_msg = f"[{count}/{limit}] {place.name} — {place.rating}"
        
        # Internal log
        logger.info(status_msg)
        
        # User visible progress line
        print(status_msg)
