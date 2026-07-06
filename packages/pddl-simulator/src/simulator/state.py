"""Runtime state models for the simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class PredicateInstance:
    """Ground predicate instance."""

    name: str
    arguments: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FluentKey:
    """Ground numeric fluent key."""

    name: str
    arguments: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RunningAction:
    """Action currently being simulated."""

    name: str
    arguments: tuple[str, ...] = ()
    started_at: Fraction = Fraction(0, 1)
    ends_at: Fraction = Fraction(0, 1)


@dataclass(slots=True)
class SimulationState:
    """Mutable simulation state."""

    time: Fraction = Fraction(0, 1)
    facts: set[PredicateInstance] = field(default_factory=set)
    numeric_values: dict[FluentKey, Fraction] = field(default_factory=dict)
    running_actions: list[RunningAction] = field(default_factory=list)

    def advance_to(self, new_time: Fraction) -> None:
        """Advance the state clock to ``new_time``."""

        if new_time < self.time:
            raise ValueError("Cannot move simulation time backwards.")
        self.time = new_time

    def holds(self, fact: PredicateInstance) -> bool:
        """Return whether a fact is true in the current state."""

        return fact in self.facts

    def set_fact(self, fact: PredicateInstance, value: bool) -> None:
        """Add or remove a ground predicate instance."""

        if value:
            self.facts.add(fact)
        else:
            self.facts.discard(fact)

    def numeric_value(self, key: FluentKey, default: Fraction = Fraction(0, 1)) -> Fraction:
        """Return a numeric fluent value, defaulting to ``0``."""

        return self.numeric_values.get(key, default)

    def set_numeric_value(self, key: FluentKey, value: Fraction) -> None:
        """Assign a numeric fluent value."""

        self.numeric_values[key] = value
