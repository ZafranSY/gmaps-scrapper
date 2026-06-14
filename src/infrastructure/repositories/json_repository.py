"""JSON Repository — infrastructure adapter for data persistence.

This module provides a concrete implementation of the RepositoryPort that saves
scaping results to a local JSON file. It handles directory creation, serialization,
and basic reporting of result data.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from src.application.dtos.scrape_request import ScrapeResult
from src.application.ports.repository_port import RepositoryPort

# Configure logging for the repository
logger = logging.getLogger(__name__)


class JsonPlaceRepository(RepositoryPort):
    """Persistence implementation using JSON files.

    The repository saves the ScrapeResult DTO to a structured JSON file.
    The output structure includes a `metadata` object (keyword, location, timing)
    and a `places` array containing serialized Place entities.

    Args:
        output_path (Path): Absolute or relative path to the destination JSON file.
    """

    def __init__(self, output_path: Path) -> None:
        """Initialise the repository with a specific file location."""
        self.output_path = Path(output_path)

    def save(self, result: ScrapeResult) -> None:
        """Save the scrape result to a pretty-printed JSON file.

        This method ensures the parent directories exist before writing. It uses
        the result's builtin export method to ensure consistency with the
        defined data schema.

        Args:
            result (ScrapeResult): The collected scrape session data.

        Raises:
            IOError: If the file cannot be written or directories cannot be created.
        """
        # Ensure parent directories exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize the session result
        payload = result.to_export_dict()
        
        # Write to JSON file with UTF-8 encoding
        with open(self.output_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            
        # Information for logs (size in KB)
        file_size_kb = self.output_path.stat().st_size / 1024.0
        
        success_msg = (
            f"Saved {result.total_collected} places → "
            f"{self.output_path} ({file_size_kb:.2f} KB)"
        )
        
        # Internal log
        logger.info(success_msg)
        
        # User visible success line
        print(f"✅ {success_msg}")
