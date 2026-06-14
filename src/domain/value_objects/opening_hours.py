"""OpeningHours value object — represents the weekly schedule.

This module stores the operation hours for each day of the week.
It is a core domain object with no external dependencies except Pydantic.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

# Module-level constant for day names to ensure consistency
DAYS_OF_WEEK = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


class OpeningHours(BaseModel):
    """Weekly opening hours for a place.

    All fields are optional and default to None.

    Attributes:
        monday (Optional[str]): Monday hours.
        tuesday (Optional[str]): Tuesday hours.
        wednesday (Optional[str]): Wednesday hours.
        thursday (Optional[str]): Thursday hours.
        friday (Optional[str]): Friday hours.
        saturday (Optional[str]): Saturday hours.
        sunday (Optional[str]): Sunday hours.
    """

    monday: Optional[str] = None
    tuesday: Optional[str] = None
    wednesday: Optional[str] = None
    thursday: Optional[str] = None
    friday: Optional[str] = None
    saturday: Optional[str] = None
    sunday: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_dict(cls, raw: dict[str, str]) -> OpeningHours:
        """Create an OpeningHours instance from a dictionary.

        Accepts lowercase day names, ignores unknown keys.

        Args:
            raw (dict[str, str]): Raw input dictionary from scraping.

        Returns:
            OpeningHours: A populated immutable instance.
        """
        data = {day: raw[day] for day in DAYS_OF_WEEK if day in raw}
        return cls(**data)

    def to_dict(self) -> dict[str, Optional[str]]:
        """Convert the value object to a plain dictionary.

        Returns:
            dict[str, Optional[str]]: A dictionary containing all 7 days.
        """
        # Ensure all 7 days are returned, even if None
        return {day: getattr(self, day) for day in DAYS_OF_WEEK}

    def is_open_today(self) -> bool:
        """Check if the place is open today based on system time.

        Uses datetime.now() to check the today's field value.

        Returns:
            bool: False if the value is None or "Closed", True otherwise.
        """
        today_name = datetime.now().strftime("%A").lower()
        today_value = getattr(self, today_name, None)

        if today_value is None:
            return False

        if today_value.strip().lower() == "closed":
            return False

        return True
