"""Execution trace support for simulator runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from .events import EventKind


@dataclass(frozen=True, slots=True)
class TraceEntry:
    """One executed simulator event."""

    time: Fraction
    kind: EventKind
    description: str


@dataclass(slots=True)
class SimulationTrace:
    """Ordered collection of executed events."""

    entries: list[TraceEntry] = field(default_factory=list)

    def record(self, entry: TraceEntry) -> None:
        """Append a trace entry."""

        self.entries.append(entry)
