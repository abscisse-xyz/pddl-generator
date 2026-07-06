"""Configuration schema for travel instances."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from .defaults import (
    DEFAULT_EXTRA_EDGES,
    DEFAULT_LOCATIONS,
    DEFAULT_MAX_TRAVEL_TIME,
    DEFAULT_MIN_TRAVEL_TIME,
)


class TravelConfig(BaseModel):
    """Validated parameters for a generated travel instance."""

    problem_name: str = "travel"
    locations: int = Field(default=DEFAULT_LOCATIONS, ge=2)
    extra_edges: int = Field(default=DEFAULT_EXTRA_EDGES, ge=0)
    min_travel_time: int = Field(default=DEFAULT_MIN_TRAVEL_TIME, ge=1)
    max_travel_time: int = Field(default=DEFAULT_MAX_TRAVEL_TIME, ge=1)
    bidirectional: bool = False
    seed: int | None = None

    @model_validator(mode="after")
    def _validate_ranges(self) -> "TravelConfig":
        if self.max_travel_time < self.min_travel_time:
            raise ValueError("max_travel_time must be greater than or equal to min_travel_time")
        max_shortcuts = (self.locations - 1) * (self.locations - 2) // 2
        if self.extra_edges > max_shortcuts:
            raise ValueError(f"extra_edges={self.extra_edges} exceeds available forward shortcuts ({max_shortcuts})")
        return self
