"""Event primitives for the event-driven simulator kernel."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import SimulationState


class EventKind(StrEnum):
    """Kinds of simulator events."""

    ACTION_START = "action_start"
    ACTION_END = "action_end"
    TIMED_EFFECT = "timed_effect"
    INTERNAL = "internal"


StateTransition = Callable[["SimulationState"], None]


@dataclass(order=True, slots=True)
class ScheduledEvent:
    """One item in the simulator event queue."""

    time: Fraction
    priority: int
    kind: EventKind = field(compare=False)
    description: str = field(compare=False)
    transition: StateTransition = field(compare=False, repr=False)
