"""Repository Port — abstract interface for persisting results.

This module defines the contract for data persistence. In the Ports and Adapters
architecture, this Port allows the application layer to save results without
knowing whether they go to a JSON file, a database, or an external API.

The benefit of this abstract port is:
1. **Persistence Agnosticism**: The core logic doesn't care about storage formats.
2. **Interchangeability**: We can swap local JSON storage for a cloud database
   (e.g., MongoDB or PostgreSQL) by simply creating a new Adapter.
3. **Clean Boundaries**: Ensures that infrastructure-specific code (like file I/O
   or database drivers) stays out of the application core.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.dtos.scrape_request import ScrapeResult


class RepositoryPort(ABC):
    """Abstract base class defining the persistence interface.

    This port must be implemented by an infrastructure adapter.
    """

    @abstractmethod
    def save(self, result: ScrapeResult) -> None:
        """Save the completed scrape result to a persistent store.

        Args:
            result (ScrapeResult): The collected data and session metadata.

        Raises:
            IOError: If the underlying storage mechanism fails to write data.
            TypeError: If the result data is incompatible with the storage format.
        """
        ...
