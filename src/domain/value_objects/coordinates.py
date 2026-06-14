"""Coordinates value object — represents geographic location.

This module handles parsing and validation of latitude/longitude pairs.
"""
from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class Coordinates(BaseModel):
    """Geographic coordinates for a place.

    Attributes:
        lat (float): Latitude value within range [-90, 90].
        lng (float): Longitude value within range [-180, 180].
    """

    lat: float
    lng: float

    model_config = ConfigDict(frozen=True)

    @field_validator("lat")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """Ensure latitude is within [-90, 90].

        Args:
            v (float): The latitude value.

        Returns:
            float: The validated latitude.

        Raises:
            ValueError: If latitude is out of range.
        """
        if not -90.0 <= v <= 90.0:
            raise ValueError(f"Latitude must be between -90 and 90, got {v}")
        return v

    @field_validator("lng")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """Ensure longitude is within [-180, 180].

        Args:
            v (float): The longitude value.

        Returns:
            float: The validated longitude.

        Raises:
            ValueError: If longitude is out of range.
        """
        if not -180.0 <= v <= 180.0:
            raise ValueError(f"Longitude must be between -180 and 180, got {v}")
        return v

    @classmethod
    def from_url(cls, url: str) -> Optional[Coordinates]:
        """Parse coordinates from a Google Maps URL.

        Looks for the '@lat,lng' pattern in the URL.

        Args:
            url (str): The full Maps URL to parse.

        Returns:
            Optional[Coordinates]: A Coordinates instance if found, else None.
        """
        # Match @ followed by lat and lng floats (handles negative values)
        match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url)
        if match:
            try:
                return cls(
                    lat=float(match.group(1)),
                    lng=float(match.group(2))
                )
            except (ValueError, TypeError):
                return None
        return None

    def __str__(self) -> str:
        """Return a string representation of the coordinates.

        Returns:
            str: The coordinates in 'lat,lng' format.
        """
        return f"{self.lat},{self.lng}"
