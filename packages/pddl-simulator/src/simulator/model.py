"""Domain/problem data models for the simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class Parameter:
    """Typed action parameter."""

    name: str
    type_name: str


@dataclass(frozen=True, slots=True)
class ObjectInstance:
    """Typed PDDL object instance."""

    name: str
    type_name: str


@dataclass(frozen=True, slots=True)
class PredicateSymbol:
    """Predicate declaration from a PDDL domain."""

    name: str
    parameter_types: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FluentSymbol:
    """Numeric fluent declaration from a PDDL domain."""

    name: str
    parameter_types: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DurativeActionSchema:
    """Normalized action schema in the simulator model.

    ``action_kind`` is either ``"durative"`` or ``"instantaneous"``.
    Runtime evaluation uses the ``source_*`` condition/effect payloads, while
    the string fields are persisted to storage for inspection and analytics.
    """

    name: str
    action_kind: str = "durative"
    parameters: tuple[Parameter, ...] = ()
    duration: Fraction = Fraction(0, 1)
    duration_expression: str = "0"
    start_conditions: tuple[str, ...] = ()
    overall_conditions: tuple[str, ...] = ()
    end_conditions: tuple[str, ...] = ()
    start_effects: tuple[str, ...] = ()
    end_effects: tuple[str, ...] = ()
    source_start_conditions: tuple[object, ...] = field(default_factory=tuple, compare=False, repr=False)
    source_overall_conditions: tuple[object, ...] = field(default_factory=tuple, compare=False, repr=False)
    source_end_conditions: tuple[object, ...] = field(default_factory=tuple, compare=False, repr=False)
    source_start_effects: tuple[object, ...] = field(default_factory=tuple, compare=False, repr=False)
    source_end_effects: tuple[object, ...] = field(default_factory=tuple, compare=False, repr=False)
    source_action: object | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class GroundedAction:
    """Ground action instance."""

    name: str
    arguments: tuple[str, ...] = ()
    parameter_bindings: tuple[tuple[str, str], ...] = ()
    duration: Fraction = Fraction(0, 1)
    schema: DurativeActionSchema | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class TimedEffect:
    """Timed problem-side effect such as a timed initial literal."""

    time: Fraction
    expression: str
    source_effect: object | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class SimulationDomain:
    """Domain-level information needed by the simulator."""

    name: str
    requirements: tuple[str, ...] = ()
    types: tuple[str, ...] = ()
    predicates: tuple[PredicateSymbol, ...] = ()
    fluents: tuple[FluentSymbol, ...] = ()
    actions: tuple[DurativeActionSchema, ...] = ()


@dataclass(frozen=True, slots=True)
class SimulationProblem:
    """Problem-level information needed by the simulator."""

    name: str
    domain_name: str
    objects: tuple[ObjectInstance, ...] = ()
    initial_facts: tuple[str, ...] = ()
    initial_numeric_values: dict[str, Fraction] = field(default_factory=dict)
    timed_effects: tuple[TimedEffect, ...] = ()
    goals: tuple[str, ...] = ()
