"""Configuration schema for sailing-TIL instances."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from .defaults import (
    DEFAULT_BOAT_POSITIONS,
    DEFAULT_CENTER_X,
    DEFAULT_CENTER_Y,
    DEFAULT_DELTA,
    DEFAULT_NUM_BOATS,
    DEFAULT_NUM_PEOPLE,
)


class SailingTilsConfig(BaseModel):
    """Validated parameters for a generated sailing-TIL instance."""

    problem_name: str = "sailing_tils"
    num_boats: int = Field(default=DEFAULT_NUM_BOATS, ge=1)
    boat_positions: tuple[float, ...] = DEFAULT_BOAT_POSITIONS
    num_people: int = Field(default=DEFAULT_NUM_PEOPLE, ge=1)
    delta: float = Field(default=DEFAULT_DELTA, gt=0)
    center_x: float = DEFAULT_CENTER_X
    center_y: float = DEFAULT_CENTER_Y

    @model_validator(mode="after")
    def _validate_positions(self) -> "SailingTilsConfig":
        if len(self.boat_positions) != self.num_boats:
            raise ValueError(
                f"boat_positions length ({len(self.boat_positions)}) must equal num_boats ({self.num_boats})"
            )
        return self
