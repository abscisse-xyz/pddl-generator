"""Configuration schema for CityCar instances."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .defaults import (
    DEFAULT_CARS,
    DEFAULT_COLUMNS,
    DEFAULT_DENSITY,
    DEFAULT_GARAGES,
    DEFAULT_MODE,
    DEFAULT_ROADS,
    DEFAULT_ROWS,
    DEFAULT_TOPOLOGY_FAMILY,
)

CityCarMode = Literal["current", "topology-first", "solution-first"]


class CityCarConfig(BaseModel):
    """Validated parameters for a generated CityCar instance."""

    problem_name: str = "citycar"
    rows: int = Field(default=DEFAULT_ROWS, ge=2)
    columns: int = Field(default=DEFAULT_COLUMNS, ge=2)
    cars: int = Field(default=DEFAULT_CARS, ge=1)
    garages: int = Field(default=DEFAULT_GARAGES, ge=1)
    roads: int = Field(default=DEFAULT_ROADS, ge=1)
    density: float = Field(default=DEFAULT_DENSITY, ge=0.0, le=1.0)
    mode: CityCarMode = DEFAULT_MODE
    topology_family: str = DEFAULT_TOPOLOGY_FAMILY
    seed: int | None = None

    @model_validator(mode="after")
    def _validate_ranges(self) -> "CityCarConfig":
        if self.garages > self.rows * self.columns:
            raise ValueError("garages must fit within the grid")
        if self.mode == "topology-first":
            if self.garages < 2:
                raise ValueError("topology-first mode requires at least two garages")
            if self.roads < max(4, self.garages):
                raise ValueError("topology-first mode requires at least four roads and enough roads for garages")
        if self.mode == "solution-first":
            if self.garages < 3:
                raise ValueError("solution-first mode requires at least three garages")
            if self.roads < max(5, self.garages + 1):
                raise ValueError("solution-first mode requires at least five roads and one non-garage route")
        return self
