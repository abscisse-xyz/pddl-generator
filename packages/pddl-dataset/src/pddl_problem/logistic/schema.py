"""Configuration schema for logistic instances."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from .defaults import (
    DEFAULT_LOCATIONS,
    DEFAULT_MAX_DISTANCE,
    DEFAULT_MAX_VELOCITY,
    DEFAULT_MIN_DISTANCE,
    DEFAULT_MIN_VELOCITY,
    DEFAULT_PACKAGES,
    DEFAULT_ROBOTS,
)


class LogisticConfig(BaseModel):
    """Validated parameters for a generated logistic instance."""

    problem_name: str = "logistic"
    locations: int = Field(default=DEFAULT_LOCATIONS, ge=2)
    robots: int = Field(default=DEFAULT_ROBOTS, ge=1)
    packages: int = Field(default=DEFAULT_PACKAGES, ge=1)
    min_distance: int = Field(default=DEFAULT_MIN_DISTANCE, ge=1)
    max_distance: int = Field(default=DEFAULT_MAX_DISTANCE, ge=1)
    min_velocity: int = Field(default=DEFAULT_MIN_VELOCITY, ge=1)
    max_velocity: int = Field(default=DEFAULT_MAX_VELOCITY, ge=1)
    seed: int | None = None

    @model_validator(mode="after")
    def _validate_ranges(self) -> "LogisticConfig":
        if self.max_distance < self.min_distance:
            raise ValueError("max_distance must be greater than or equal to min_distance")
        if self.max_velocity < self.min_velocity:
            raise ValueError("max_velocity must be greater than or equal to min_velocity")
        return self
