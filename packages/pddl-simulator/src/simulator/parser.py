"""Parser abstraction for loading PDDL into simulator models."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

from unified_planning.io import PDDLReader

from .model import (
    DurativeActionSchema,
    FluentSymbol,
    GroundedAction,
    ObjectInstance,
    Parameter,
    PredicateSymbol,
    SimulationDomain,
    SimulationProblem,
    TimedEffect,
)
from .state import FluentKey, PredicateInstance, SimulationState


@dataclass(frozen=True, slots=True)
class PDDLSource:
    """PDDL source files for one simulation instance."""

    domain_path: Path
    problem_path: Path


@dataclass(frozen=True, slots=True)
class ParsedSimulation:
    """Parsed simulation bundle ready to initialize the runtime."""

    domain: SimulationDomain
    problem: SimulationProblem
    initial_state: SimulationState
    grounded_actions: tuple[GroundedAction, ...] = ()
    source_problem: object | None = field(default=None, compare=False, repr=False)


class UnifiedPlanningParser:
    """Load a PDDL domain/problem pair through unified-planning."""

    def __init__(self, reader: PDDLReader | None = None) -> None:
        self._reader = reader or PDDLReader()

    def load(self, source: PDDLSource) -> tuple[SimulationDomain, SimulationProblem]:
        """Load a domain/problem pair into simulator models."""

        runtime = self.load_runtime(source)
        return runtime.domain, runtime.problem

    def load_runtime(self, source: PDDLSource) -> ParsedSimulation:
        """Load and ground a domain/problem pair for simulation."""

        problem = self._reader.parse_problem(str(source.domain_path), str(source.problem_path))
        domain_name = self._extract_domain_name(source.domain_path)

        object_instances = tuple(
            ObjectInstance(name=obj.name, type_name=self._type_name(obj.type)) for obj in problem.all_objects
        )

        initial_fact_names: list[str] = []
        initial_numeric_names: dict[str, Fraction] = {}
        initial_state = SimulationState()
        for fluent_exp, value_exp in problem.initial_values.items():
            if value_exp.is_bool_constant():
                if value_exp.bool_constant_value():
                    fact = PredicateInstance(
                        name=fluent_exp.fluent().name,
                        arguments=tuple(self._argument_name(argument) for argument in fluent_exp.args),
                    )
                    initial_state.set_fact(fact, True)
                    initial_fact_names.append(str(fluent_exp))
            else:
                key = FluentKey(
                    name=fluent_exp.fluent().name,
                    arguments=tuple(self._argument_name(argument) for argument in fluent_exp.args),
                )
                numeric_value = self._fraction_from_constant(value_exp)
                initial_state.set_numeric_value(key, numeric_value)
                initial_numeric_names[str(fluent_exp)] = numeric_value

        domain_actions: list[DurativeActionSchema] = []
        schema_by_name: dict[str, DurativeActionSchema] = {}
        for action in problem.actions:
            schema = self._normalize_action_schema(action=action, initial_state=initial_state)
            domain_actions.append(schema)
            schema_by_name[schema.name] = schema

        predicate_symbols: list[PredicateSymbol] = []
        fluent_symbols: list[FluentSymbol] = []
        for fluent in problem.fluents:
            parameter_types = tuple(self._type_name(parameter.type) for parameter in fluent.signature)
            if fluent.type.is_bool_type():
                predicate_symbols.append(PredicateSymbol(name=fluent.name, parameter_types=parameter_types))
            else:
                fluent_symbols.append(FluentSymbol(name=fluent.name, parameter_types=parameter_types))

        timed_effects: list[TimedEffect] = []
        for timing, effects in problem.timed_effects.items():
            event_time = self._fraction_from_number(timing.delay)
            for effect in effects:
                timed_effects.append(TimedEffect(time=event_time, expression=str(effect), source_effect=effect))

        domain = SimulationDomain(
            name=domain_name,
            requirements=self._requirements(problem.kind.features),
            types=tuple(sorted({instance.type_name for instance in object_instances})),
            predicates=tuple(predicate_symbols),
            fluents=tuple(fluent_symbols),
            actions=tuple(domain_actions),
        )
        simulation_problem = SimulationProblem(
            name=problem.name,
            domain_name=domain_name,
            objects=object_instances,
            initial_facts=tuple(initial_fact_names),
            initial_numeric_values=initial_numeric_names,
            timed_effects=tuple(sorted(timed_effects, key=lambda effect: effect.time)),
            goals=self._goal_strings(problem.goals),
        )
        return ParsedSimulation(
            domain=domain,
            problem=simulation_problem,
            initial_state=initial_state,
            grounded_actions=(),
            source_problem=problem,
        )

    def _normalize_action_schema(self, action, initial_state: SimulationState) -> DurativeActionSchema:
        parameters = tuple(
            Parameter(name=parameter.name, type_name=self._type_name(parameter.type)) for parameter in action.parameters
        )

        if hasattr(action, "duration"):
            source_start_conditions = self._conditions_for_interval_objects(action.conditions.items(), "[start]")
            source_overall_conditions = self._conditions_for_interval_objects(action.conditions.items(), "(start, end)")
            source_end_conditions = self._conditions_for_interval_objects(action.conditions.items(), "[end]")
            source_start_effects = self._effects_for_timing_objects(action.effects.items(), "start")
            source_end_effects = self._effects_for_timing_objects(action.effects.items(), "end")
            return DurativeActionSchema(
                name=action.name,
                action_kind="durative",
                parameters=parameters,
                duration=self._evaluate_numeric_expression(action.duration.lower, state=initial_state, bindings={}),
                duration_expression=str(action.duration.lower),
                start_conditions=tuple(str(condition) for condition in source_start_conditions),
                overall_conditions=tuple(str(condition) for condition in source_overall_conditions),
                end_conditions=tuple(str(condition) for condition in source_end_conditions),
                start_effects=tuple(str(effect) for effect in source_start_effects),
                end_effects=tuple(str(effect) for effect in source_end_effects),
                source_start_conditions=source_start_conditions,
                source_overall_conditions=source_overall_conditions,
                source_end_conditions=source_end_conditions,
                source_start_effects=source_start_effects,
                source_end_effects=source_end_effects,
                source_action=action,
            )

        source_start_conditions = tuple(action.preconditions)
        source_start_effects = tuple(action.effects)
        return DurativeActionSchema(
            name=action.name,
            action_kind="instantaneous",
            parameters=parameters,
            duration=Fraction(0, 1),
            duration_expression="0",
            start_conditions=tuple(str(condition) for condition in source_start_conditions),
            overall_conditions=(),
            end_conditions=(),
            start_effects=tuple(str(effect) for effect in source_start_effects),
            end_effects=(),
            source_start_conditions=source_start_conditions,
            source_overall_conditions=(),
            source_end_conditions=(),
            source_start_effects=source_start_effects,
            source_end_effects=(),
            source_action=action,
        )

    def _conditions_for_interval(self, condition_items, expected_interval: str) -> tuple[str, ...]:
        return tuple(
            str(condition)
            for interval, conditions in condition_items
            if str(interval) == expected_interval
            for condition in conditions
        )

    def _conditions_for_interval_objects(self, condition_items, expected_interval: str) -> tuple[object, ...]:
        return tuple(
            condition
            for interval, conditions in condition_items
            if str(interval) == expected_interval
            for condition in conditions
        )

    def _effects_for_timing(self, effect_items, expected_timing: str) -> tuple[str, ...]:
        return tuple(
            str(effect) for timing, effects in effect_items if str(timing) == expected_timing for effect in effects
        )

    def _effects_for_timing_objects(self, effect_items, expected_timing: str) -> tuple[object, ...]:
        return tuple(effect for timing, effects in effect_items if str(timing) == expected_timing for effect in effects)

    def _goal_strings(self, goals) -> tuple[str, ...]:
        flattened: list[str] = []
        for goal in goals:
            if goal.is_and():
                flattened.extend(str(argument) for argument in goal.args)
            else:
                flattened.append(str(goal))
        return tuple(flattened)

    def _evaluate_numeric_expression(
        self,
        expression,
        state: SimulationState,
        bindings: dict[str, str],
    ) -> Fraction:
        if expression.is_int_constant():
            return Fraction(expression.int_constant_value(), 1)
        if expression.is_real_constant():
            return self._fraction_from_number(expression.real_constant_value())
        if expression.is_fluent_exp():
            key = FluentKey(
                name=expression.fluent().name,
                arguments=tuple(self._argument_name(argument, bindings) for argument in expression.args),
            )
            return state.numeric_value(key)
        if expression.is_plus():
            return sum(
                (self._evaluate_numeric_expression(argument, state, bindings) for argument in expression.args),
                start=Fraction(0, 1),
            )
        if expression.is_minus():
            if len(expression.args) == 1:
                return -self._evaluate_numeric_expression(expression.arg(0), state, bindings)
            left = self._evaluate_numeric_expression(expression.arg(0), state, bindings)
            right = self._evaluate_numeric_expression(expression.arg(1), state, bindings)
            return left - right
        raise NotImplementedError(f"Unsupported numeric expression while parsing: {expression}")

    def _requirements(self, features) -> tuple[str, ...]:
        return tuple(sorted(getattr(feature, "name", str(feature)).lower() for feature in features))

    def _type_name(self, type_) -> str:
        return getattr(type_, "name", str(type_))

    def _argument_name(self, argument, bindings: dict[str, str] | None = None) -> str:
        bindings = bindings or {}
        if argument.is_object_exp():
            return argument.object().name
        if argument.is_parameter_exp():
            return bindings.get(argument.parameter().name, argument.parameter().name)
        raise NotImplementedError(f"Unsupported argument expression: {argument}")

    def _fraction_from_constant(self, expression) -> Fraction:
        if expression.is_int_constant():
            return Fraction(expression.int_constant_value(), 1)
        if expression.is_real_constant():
            return self._fraction_from_number(expression.real_constant_value())
        raise TypeError(f"Expected a numeric constant, got: {expression}")

    def _fraction_from_number(self, value) -> Fraction:
        if isinstance(value, Fraction):
            return value
        if isinstance(value, int):
            return Fraction(value, 1)
        return Fraction(str(value))

    def _extract_domain_name(self, domain_path: Path) -> str:
        for line in domain_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("(define (domain ") and stripped.endswith(")"):
                return stripped[len("(define (domain ") : -1]
        return domain_path.stem
