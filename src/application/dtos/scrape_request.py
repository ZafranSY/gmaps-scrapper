"""DTOs for the scraping application.

Includes the ScrapeRequest (input) and ScrapeResult (output) classes.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, field_validator

from src.domain.entities.place import Place


class ScrapeRequest(BaseModel):
    """Input request for a scraping session.

    Attributes:
        keyword (str): The term to search for.
        location (str): The location for the search.
        limit (int): Max places to collect.
        output_path (Path): Where to save results.
        headless (bool): Browser mode.
        verbose (bool): Logging level.
    """

    keyword: str
    location: str
    limit: int = 200
    output_path: Path = Path("results.json")
    headless: bool = False
    verbose: bool = False

    @field_validator("keyword")
    @classmethod
    def validate_keyword(cls, v: str) -> str:
        """Ensure keyword is not empty."""
        if not v.strip():
            raise ValueError("Keyword cannot be empty")
        return v.strip()

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Ensure location is not empty."""
        if not v.strip():
            raise ValueError("Location cannot be empty")
        return v.strip()

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        """Allow 0 or -1 for unlimited, otherwise cap at 1000."""
        if v <= 0:
            return v  # 0 or -1 means unlimited
        return min(v, 1000)

    @property
    def query(self) -> str:
        """Construct the search query.

        Returns:
            str: The full query string.
        """
        return f"{self.keyword} {self.location}"


class ScrapeResult(BaseModel):
    """Output result of a scraping session.

    Attributes:
        request (ScrapeRequest): The original request.
        places (List[Place]): List of extracted places.
        started_at (datetime): Session start timestamp.
        finished_at (Optional[datetime]): Session finish timestamp.
    """

    request: ScrapeRequest
    places: List[Place] = []
    started_at: datetime
    finished_at: Optional[datetime] = None

    @property
    def total_collected(self) -> int:
        """Count of places collected.

        Returns:
            int: The total count.
        """
        return len(self.places)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate the duration of the scrape.

        Returns:
            Optional[float]: Duration in seconds, or None if not finished.
        """
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    def to_export_dict(self) -> dict:
        """Export the result to a serializable dictionary.

        Returns:
            dict: The completed session data with metadata and places.
        """
        return {
            "metadata": {
                "query": self.request.query,
                "keyword": self.request.keyword,
                "location": self.request.location,
                "limit": self.request.limit,
                "total_collected": self.total_collected,
                "started_at": self.started_at.isoformat(),
                "finished_at": self.finished_at.isoformat() if self.finished_at else None,
                "duration_seconds": self.duration_seconds,
            },
            "places": [place.to_export_dict() for place in self.places],
        }
