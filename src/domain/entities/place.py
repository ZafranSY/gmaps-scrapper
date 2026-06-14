"""Place entity — the central domain object.

This module defines the Place entity which represents a single Google Maps listing.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.value_objects.coordinates import Coordinates
from src.domain.value_objects.opening_hours import OpeningHours


class Place(BaseModel):
    """Core domain entity representing a Google Maps place.

    Attributes:
        place_id (str): Unique identifier (UUID4 by default).
        name (str): The name of the place (required, non-empty).
        category (Optional[str]): Primary category.
        rating (Optional[float]): Numeric rating [0.0, 5.0].
        reviews_count (Optional[int]): Total reviews (>= 0).
        price_level (Optional[str]): Price indicator (e.g., "$", "$$").
        address (Optional[str]): Formatted address.
        phone (Optional[str]): Contact number.
        website (Optional[str]): Official URL.
        website_classification (Optional[str]): Outreach signal (e.g., "linktree", "whatsapp").
        opening_hours (Optional[OpeningHours]): Weekly schedule.
        coordinates (Optional[Coordinates]): Lat/Lng location.
        photos_urls (List[str]): List of photo links.
        plus_code (Optional[str]): Google Plus Code.
        scraped_at (datetime): When the data was extracted.
    """

    place_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(...)
    category: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    price_level: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    website_classification: Optional[str] = None
    opening_hours: Optional[OpeningHours] = None
    coordinates: Optional[Coordinates] = None
    photos_urls: List[str] = Field(default_factory=list)
    plus_code: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=False)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not empty after stripping whitespace.

        Args:
            v (str): The name value.

        Returns:
            str: The validated name.

        Raises:
            ValueError: If name is empty.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("Name cannot be empty")
        return stripped

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: Optional[float]) -> Optional[float]:
        """Ensure rating is within [0.0, 5.0].

        Args:
            v (Optional[float]): The rating value.

        Returns:
            Optional[float]: The validated rating.

        Raises:
            ValueError: If rating is out of range.
        """
        if v is not None and not 0.0 <= v <= 5.0:
            raise ValueError(f"Rating must be between 0.0 and 5.0, got {v}")
        return v

    @field_validator("reviews_count")
    @classmethod
    def validate_reviews_count(cls, v: Optional[int]) -> Optional[int]:
        """Ensure reviews_count is non-negative.

        Args:
            v (Optional[int]): The reviews count.

        Returns:
            Optional[int]: The validated reviews count.

        Raises:
            ValueError: If reviews_count is negative.
        """
        if v is not None and v < 0:
            raise ValueError(f"Reviews count must be non-negative, got {v}")
        return v

    def to_export_dict(self) -> dict:
        """Serialize the entity to a fully JSON-serializable dictionary.

        Returns:
            dict: The dictionary representation of the place.
        """
        data = self.model_dump()
        data["scraped_at"] = self.scraped_at.isoformat()
        
        if self.coordinates:
            data["coordinates"] = {
                "lat": self.coordinates.lat,
                "lng": self.coordinates.lng
            }
            
        if self.opening_hours:
            data["opening_hours"] = self.opening_hours.to_dict()
            
        return data

    def __repr__(self) -> str:
        """Return a string representation showing name and rating.

        Returns:
            str: Representation of the place.
        """
        return f"Place(name='{self.name}', rating={self.rating})"
