"""Event-driven simulation kernel.

Convenience helpers on :class:`SimulatorEngine` are ergonomic wrappers for
callers; planner replay and simulation persistence should continue to use the
explicit lifecycle methods they already depend on.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING

from .events import EventKind, ScheduledEvent
from .model import GroundedAction, SimulationDomain, SimulationProblem
from .parser import ParsedSimulation, PDDLSource, UnifiedPlanningParser
from .persistence import StateStore
from .state import FluentKey, PredicateInstance, RunningAction, SimulationState
from .trace import SimulationTrace, TraceEntry

if TYPE_CHECKING:
    from unified_planning.model.fnode import FNode
    from unified_planning.plans import ActionInstance, Plan


@dataclass(slots=True)
class SimulatorEngine:
    """Event-driven runtime for the supported temporal PDDL subset."""

    initial_state: SimulationState = field(default_factory=SimulationState)
    state: SimulationState = field(default_factory=SimulationState)
    trace: SimulationTrace = field(default_factory=SimulationTrace)
    domain: SimulationDomain | None = None
    problem: SimulationProblem | None = None
    grounded_actions: tuple[GroundedAction, ...] = ()
    source_problem: object | None = field(default=None, repr=False)
    state_store: StateStore | None = field(default=None, repr=False)
    run_id: int | None = field(default=None, init=False)
    _prepared_run_id: int | None = field(default=None, init=False, repr=False)
    step_index: int = field(default=0, init=False)
    _queue: list[ScheduledEvent] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.reset()

    @classmethod
    def from_runtime(cls, runtime: ParsedSimulation) -> SimulatorEngine:
        """Create an engine from a parsed runtime bundle."""

        return cls(
            initial_state=runtime.initial_state,
            domain=runtime.domain,
            problem=runtime.problem,
            grounded_actions=runtime.grounded_actions,
            source_problem=runtime.source_problem,
        )

    @classmethod
    def from_pddl(
        cls,
        domain_path: str | Path,
        problem_path: str | Path,
        parser: UnifiedPlanningParser | None = None,
    ) -> SimulatorEngine:
        """Load a domain/problem pair and construct a simulator engine."""

        runtime = (parser or UnifiedPlanningParser()).load_runtime(
            PDDLSource(domain_path=Path(domain_path), problem_path=Path(problem_path))
        )
        return cls.from_runtime(runtime)

    def reset(self) -> None:
        """Reset the runtime to the configured initial state."""

        self.state = SimulationState(
            time=self.initial_state.time,
            facts=set(self.initial_state.facts),
            numeric_values=dict(self.initial_state.numeric_values),
            running_actions=list(self.initial_state.running_actions),
        )
        self.trace = SimulationTrace()
        self._queue = []
        self.step_index = 0
        self._schedule_problem_timed_effects()
        self._start_persisted_run()
        self._persist_snapshot("reset")

    def schedule(self, event: ScheduledEvent) -> None:
        """Push a future event into the queue."""

        if event.time < self.state.time:
            raise ValueError("Cannot schedule an event in the past.")
        heapq.heappush(self._queue, event)

    def has_pending_events(self) -> bool:
        """Return whether the runtime still has scheduled work."""

        return bool(self._queue)

    def step(self) -> ScheduledEvent | None:
        """Execute the next scheduled event, if any."""

        if not self._queue:
            return None

        event = heapq.heappop(self._queue)
        self.state.advance_to(event.time)
        event.transition(self.state)
        trace_entry = TraceEntry(time=event.time, kind=event.kind, description=event.description)
        self.trace.record(trace_entry)
        self.step_index += 1
        self._persist_trace_entry(trace_entry)
        self._persist_snapshot(event.kind.value)
        return event

    def run_until(self, target_time: Fraction) -> None:
        """Execute all events up to ``target_time`` and advance the clock."""

        previous_time = self.state.time
        while self._queue and self._queue[0].time <= target_time:
            self.step()
        self.state.advance_to(target_time)
        if self.state.time > previous_time and not (
            self.trace.entries and self.trace.entries[-1].time == self.state.time
        ):
            self.step_index += 1
            self._persist_snapshot("time_advance")

    def run_to_completion(self, max_steps: int | None = None) -> int:
        """Execute pending events until the queue is empty."""

        executed = 0
        while self._queue:
            if max_steps is not None and executed >= max_steps:
                raise RuntimeError("Maximum number of simulator steps reached.")
            self.step()
            executed += 1
        return executed

    def applicable_actions(self) -> tuple[GroundedAction, ...]:
        """Return currently applicable grounded durative actions."""

        return tuple(action for action in self._iter_grounded_actions() if self._action_start_conditions_hold(action))

    def apply_action(
        self,
        action_name: str,
        arguments: tuple[str, ...] = (),
        *,
        finish: bool = True,
    ) -> GroundedAction:
        """Start an action and optionally advance to that action's end time.

        Assumption: ``finish=True`` completes only the action just started by
        advancing to ``start_time + duration``; it does not drain unrelated
        pending events beyond that horizon.
        """

        start_time = self.state.time
        action = self.start_action(action_name, arguments)
        if finish:
            self.run_until(start_time + action.duration)
        return action

    def current_facts(self) -> tuple[tuple[str, ...], ...]:
        """Return current boolean facts as sorted flat predicate tuples.

        Assumption: the tuple shape is ``(predicate_name, *arguments)`` and
        intentionally excludes numeric fluents and running-action metadata.
        """

        return tuple(sorted((fact.name, *fact.arguments) for fact in self.state.facts))

    def start_action(self, action_name: str, arguments: tuple[str, ...] = ()) -> GroundedAction:
        """Start a grounded durative action at the current simulation time."""

        action = self._find_grounded_action(action_name, arguments)
        if not self._action_start_conditions_hold(action):
            raise ValueError(f"Action {action_name}{arguments!r} is not applicable at time {self.state.time}.")

        if action.schema is not None and action.schema.action_kind == "instantaneous":
            self._apply_action_effects(action, timing="start")
            self.trace.record(
                TraceEntry(
                    time=self.state.time,
                    kind=EventKind.ACTION_START,
                    description=self._action_description(action, "apply"),
                )
            )
            self.step_index += 1
            self._persist_trace_entry(self.trace.entries[-1])
            self._persist_action_event(action, phase="apply", sim_time=self.state.time, step_index=self.step_index)
            self._persist_snapshot("action_apply")
            return action

        running_action = RunningAction(
            name=action.name,
            arguments=action.arguments,
            started_at=self.state.time,
            ends_at=self.state.time + action.duration,
        )
        self.state.running_actions.append(running_action)
        self._apply_action_effects(action, timing="start")
        self.trace.record(
            TraceEntry(
                time=self.state.time,
                kind=EventKind.ACTION_START,
                description=self._action_description(action, "start"),
            )
        )
        self.step_index += 1
        self._persist_trace_entry(self.trace.entries[-1])
        self._persist_action_event(action, phase="start", sim_time=self.state.time, step_index=self.step_index)
        self.schedule(
            ScheduledEvent(
                time=running_action.ends_at,
                priority=10,
                kind=EventKind.ACTION_END,
                description=self._action_description(action, "end"),
                transition=lambda state, grounded_action=action: self._finish_action(grounded_action, state),
            )
        )
        self._persist_snapshot(EventKind.ACTION_START.value)
        return action

    def replay_plan(
        self,
        plan: Plan,
        *,
        reset: bool = True,
        finish_pending_events: bool = False,
    ) -> SimulationState:
        """Replay a unified-planning plan against the simulator runtime.

        Supported plan kinds are:

        - `SequentialPlan`
        - `TimeTriggeredPlan`

        By default, replay stops at the plan horizon so callers can keep
        simulating incrementally from the returned state. Set
        ``finish_pending_events`` to ``True`` to drain the event queue after the
        plan has been replayed.
        """

        if reset:
            self.reset()

        plan_type_name = type(plan).__name__
        plan_horizon = self.state.time
        if plan_type_name == "HierarchicalPlan":
            # Hierarchical plans wrap an executable flat plan; recurse on it.
            # The decomposition (method instances) is not yet captured in the trace.
            inner = getattr(plan, "action_plan", None)
            if inner is None:
                raise ValueError("HierarchicalPlan has no `action_plan` attribute to replay.")
            return self.replay_plan(inner, reset=False, finish_pending_events=finish_pending_events)
        if plan_type_name == "SequentialPlan":
            for action_instance in plan.actions:
                grounded_action = self._start_action_instance(action_instance)
                self.run_until(self.state.time + grounded_action.duration)
                plan_horizon = self.state.time
        elif plan_type_name == "TimeTriggeredPlan":
            for start_time, action_instance, duration in plan.timed_actions:
                target_time = self._fraction_from_number(start_time)
                self.run_until(target_time)
                grounded_action = self._start_action_instance(action_instance)
                action_end_time = target_time + grounded_action.duration
                if action_end_time > plan_horizon:
                    plan_horizon = action_end_time
                if duration is not None and self._fraction_from_number(duration) != grounded_action.duration:
                    raise ValueError(
                        "Plan duration does not match grounded action duration for "
                        f"{grounded_action.name}{grounded_action.arguments!r}."
                    )
        else:
            raise NotImplementedError(
                f"Unsupported plan type for replay: {plan_type_name!r}. "
                f"Supported: SequentialPlan, TimeTriggeredPlan, HierarchicalPlan (over either). "
                f"PartialOrderPlan / STNPlan / ContingentPlan are not yet replayable; "
                f"linearize or schedule them first."
            )

        self.run_until(plan_horizon)
        if finish_pending_events:
            self.run_to_completion()
        return self.state

    def goals_satisfied(self) -> bool:
        """Return whether all problem goals hold in the current state."""

        if self.source_problem is None:
            return False
        return all(self._evaluate_boolean(goal, {}) for goal in self.source_problem.goals)

    def _find_grounded_action(self, action_name: str, arguments: tuple[str, ...]) -> GroundedAction:
        for action in self.grounded_actions:
            if action.name == action_name and action.arguments == arguments:
                return action
        return self._ground_action(action_name, arguments)

    def _ground_action(self, action_name: str, arguments: tuple[str, ...]) -> GroundedAction:
        schema = self._find_action_schema(action_name)
        if len(arguments) != len(schema.parameters):
            raise KeyError(
                f"Unknown grounded action: {action_name}{arguments!r}; expected {len(schema.parameters)} argument(s)."
            )

        objects_by_name = {obj.name: obj for obj in self.problem.objects} if self.problem is not None else {}
        bindings: dict[str, str] = {}
        for parameter, argument in zip(schema.parameters, arguments, strict=True):
            object_instance = objects_by_name.get(argument)
            if object_instance is None or object_instance.type_name != parameter.type_name:
                raise KeyError(f"Unknown grounded action: {action_name}{arguments!r}")
            bindings[parameter.name] = argument

        duration = schema.duration
        if schema.action_kind == "durative":
            duration = self._evaluate_numeric(schema.source_action.duration.lower, bindings)
        return GroundedAction(
            name=schema.name,
            arguments=arguments,
            parameter_bindings=tuple(bindings.items()),
            duration=duration,
            schema=schema,
        )

    def _iter_grounded_actions(self):
        if self.grounded_actions:
            yield from self.grounded_actions
            return
        if self.domain is None or self.problem is None:
            return

        objects_by_type = {
            type_name: tuple(obj for obj in self.problem.objects if obj.type_name == type_name)
            for type_name in {obj.type_name for obj in self.problem.objects}
        }
        for schema in self.domain.actions:
            if not schema.parameters:
                yield self._ground_action(schema.name, ())
                continue
            parameter_domains = [objects_by_type.get(parameter.type_name, ()) for parameter in schema.parameters]
            for object_tuple in product(*parameter_domains):
                yield self._ground_action(schema.name, tuple(obj.name for obj in object_tuple))

    def _find_action_schema(self, action_name: str):
        if self.domain is None:
            raise KeyError(f"Unknown grounded action: {action_name!r}")
        for schema in self.domain.actions:
            if schema.name == action_name:
                return schema
        raise KeyError(f"Unknown grounded action: {action_name!r}")

    def _start_action_instance(self, action_instance: ActionInstance) -> GroundedAction:
        arguments = tuple(self._resolve_argument(argument, {}) for argument in action_instance.actual_parameters)
        return self.start_action(action_instance.action.name, arguments)

    def _schedule_problem_timed_effects(self) -> None:
        if self.problem is None:
            return
        for timed_effect in self.problem.timed_effects:
            self.schedule(
                ScheduledEvent(
                    time=timed_effect.time,
                    priority=20,
                    kind=EventKind.TIMED_EFFECT,
                    description=f"timed-effect {timed_effect.expression}",
                    transition=lambda state, effect=timed_effect.source_effect: self._apply_effect(effect, {}, state),
                )
            )

    def _finish_action(self, action: GroundedAction, state: SimulationState) -> None:
        self._assert_action_end_conditions(action)
        self._apply_action_effects(action, timing="end")
        state.running_actions = [
            running
            for running in state.running_actions
            if not (running.name == action.name and running.arguments == action.arguments)
        ]
        self._persist_action_event(action, phase="end", sim_time=state.time, step_index=self.step_index + 1)

    def _action_start_conditions_hold(self, action: GroundedAction) -> bool:
        schema = self._require_schema(action)
        bindings = dict(action.parameter_bindings)
        return all(self._evaluate_boolean(condition, bindings) for condition in schema.source_start_conditions)

    def _assert_action_end_conditions(self, action: GroundedAction) -> None:
        schema = self._require_schema(action)
        bindings = dict(action.parameter_bindings)
        failed = [
            str(condition)
            for condition in schema.source_end_conditions
            if not self._evaluate_boolean(condition, bindings)
        ]
        if failed:
            raise RuntimeError(
                f"End conditions failed for {action.name}{action.arguments!r} at time {self.state.time}: {failed}"
            )

    def _apply_action_effects(self, action: GroundedAction, timing: str) -> None:
        schema = self._require_schema(action)
        bindings = dict(action.parameter_bindings)
        effects = schema.source_start_effects if timing == "start" else schema.source_end_effects
        for effect in effects:
            self._apply_effect(effect, bindings, self.state)

    def _apply_effect(self, effect, bindings: dict[str, str], state: SimulationState) -> None:
        if effect.is_forall():
            for quantified_bindings in self._quantified_effect_bindings(effect, bindings):
                self._apply_effect_instance(effect, quantified_bindings, state)
            return

        self._apply_effect_instance(effect, bindings, state)

    def _apply_effect_instance(self, effect, bindings: dict[str, str], state: SimulationState) -> None:
        if not self._evaluate_boolean(effect.condition, bindings, state=state):
            return

        target = effect.fluent
        arguments = tuple(self._resolve_argument(argument, bindings) for argument in target.args)
        if target.type.is_bool_type():
            state.set_fact(
                PredicateInstance(name=target.fluent().name, arguments=arguments),
                self._evaluate_boolean(effect.value, bindings, state=state),
            )
            return

        key = FluentKey(name=target.fluent().name, arguments=arguments)
        value = self._evaluate_numeric(effect.value, bindings, state=state)
        if effect.is_assignment():
            state.set_numeric_value(key, value)
        elif effect.is_increase():
            state.set_numeric_value(key, state.numeric_value(key) + value)
        elif effect.is_decrease():
            state.set_numeric_value(key, state.numeric_value(key) - value)
        else:  # pragma: no cover
            raise NotImplementedError(f"Unsupported effect kind: {effect}")

    def _quantified_effect_bindings(self, effect, bindings: dict[str, str]):
        if self.problem is None:
            return
        quantified_parameters = tuple(effect.forall)
        objects_by_type = {
            type_name: tuple(obj.name for obj in self.problem.objects if obj.type_name == type_name)
            for type_name in {obj.type_name for obj in self.problem.objects}
        }
        parameter_domains = [
            objects_by_type.get(getattr(parameter.type, "name", str(parameter.type)), ())
            for parameter in quantified_parameters
        ]
        for object_tuple in product(*parameter_domains):
            extended = dict(bindings)
            for parameter, object_name in zip(quantified_parameters, object_tuple, strict=True):
                extended[parameter.name] = object_name
            yield extended

    def _evaluate_boolean(
        self,
        expression: FNode,
        bindings: dict[str, str],
        state: SimulationState | None = None,
    ) -> bool:
        state = state or self.state
        if expression.is_bool_constant():
            return expression.bool_constant_value()
        if expression.is_and():
            return all(self._evaluate_boolean(argument, bindings, state) for argument in expression.args)
        if expression.is_or():
            return any(self._evaluate_boolean(argument, bindings, state) for argument in expression.args)
        if expression.is_not():
            return not self._evaluate_boolean(expression.arg(0), bindings, state)
        if expression.is_fluent_exp() and expression.type.is_bool_type():
            return state.holds(
                PredicateInstance(
                    name=expression.fluent().name,
                    arguments=tuple(self._resolve_argument(argument, bindings) for argument in expression.args),
                )
            )
        if expression.is_le():
            return self._evaluate_numeric(expression.arg(0), bindings, state) <= self._evaluate_numeric(
                expression.arg(1), bindings, state
            )
        if expression.is_lt():
            return self._evaluate_numeric(expression.arg(0), bindings, state) < self._evaluate_numeric(
                expression.arg(1), bindings, state
            )
        if expression.is_equals():
            left = self._evaluate_scalar(expression.arg(0), bindings, state)
            right = self._evaluate_scalar(expression.arg(1), bindings, state)
            return left == right
        raise NotImplementedError(f"Unsupported boolean expression: {expression}")

    def _evaluate_numeric(
        self,
        expression: FNode,
        bindings: dict[str, str],
        state: SimulationState | None = None,
    ) -> Fraction:
        state = state or self.state
        if expression.is_int_constant():
            return Fraction(expression.int_constant_value(), 1)
        if expression.is_real_constant():
            return self._fraction_from_number(expression.real_constant_value())
        if expression.is_fluent_exp():
            return state.numeric_value(
                FluentKey(
                    name=expression.fluent().name,
                    arguments=tuple(self._resolve_argument(argument, bindings) for argument in expression.args),
                )
            )
        if expression.is_plus():
            return sum(
                (self._evaluate_numeric(argument, bindings, state) for argument in expression.args),
                start=Fraction(0, 1),
            )
        if expression.is_minus():
            if len(expression.args) == 1:
                return -self._evaluate_numeric(expression.arg(0), bindings, state)
            return self._evaluate_numeric(expression.arg(0), bindings, state) - self._evaluate_numeric(
                expression.arg(1), bindings, state
            )
        raise NotImplementedError(f"Unsupported numeric expression: {expression}")

    def _evaluate_scalar(
        self,
        expression: FNode,
        bindings: dict[str, str],
        state: SimulationState | None = None,
    ) -> object:
        if expression.is_object_exp() or expression.is_parameter_exp():
            return self._resolve_argument(expression, bindings)
        if expression.type.is_bool_type():
            return self._evaluate_boolean(expression, bindings, state)
        return self._evaluate_numeric(expression, bindings, state)

    def _resolve_argument(self, argument: FNode, bindings: dict[str, str]) -> str:
        if argument.is_object_exp():
            return argument.object().name
        if argument.is_parameter_exp():
            return bindings[argument.parameter().name]
        if argument.is_variable_exp():
            return bindings[argument.variable().name]
        raise NotImplementedError(f"Unsupported action argument expression: {argument}")

    def _require_schema(self, action: GroundedAction):
        if action.schema is None:
            raise RuntimeError(f"Grounded action {action.name} is missing its schema payload.")
        return action.schema

    def _action_description(self, action: GroundedAction, phase: str) -> str:
        args = ", ".join(action.arguments)
        return f"{phase} {action.name}({args})"

    def _fraction_from_number(self, value) -> Fraction:
        if isinstance(value, Fraction):
            return value
        if isinstance(value, int):
            return Fraction(value, 1)
        return Fraction(str(value))

    def _start_persisted_run(self) -> None:
        if self.state_store is None:
            self.run_id = None
            return
        if self._prepared_run_id is not None:
            self.run_id = self._prepared_run_id
            self._prepared_run_id = None
        else:
            run = self.state_store.create_run(
                domain_name=self.domain.name if self.domain is not None else None,
                problem_name=self.problem.name if self.problem is not None else None,
            )
            self.run_id = run.run_id
        if self.run_id is not None and self.domain is not None and self.problem is not None:
            self.state_store.persist_problem_model(
                run_id=self.run_id,
                domain=self.domain,
                problem=self.problem,
            )

    def prepare_persisted_run(self, run_id: int) -> None:
        """Reuse an already-created persistence run on the next reset()."""

        self._prepared_run_id = run_id

    def _persist_trace_entry(self, entry: TraceEntry) -> None:
        if self.state_store is None or self.run_id is None:
            return
        self.state_store.append_trace_entry(run_id=self.run_id, step_index=self.step_index, entry=entry)

    def _persist_snapshot(self, reason: str) -> None:
        if self.state_store is None or self.run_id is None:
            return
        self.state_store.save_snapshot(
            run_id=self.run_id,
            step_index=self.step_index,
            sim_time=self.state.time,
            reason=reason,
            state=self.state,
            pending_events=tuple(self._queue),
        )

    def _persist_action_event(self, action: GroundedAction, *, phase: str, sim_time: Fraction, step_index: int) -> None:
        if self.state_store is None or self.run_id is None:
            return
        self.state_store.append_action_event(
            run_id=self.run_id,
            step_index=step_index,
            sim_time=sim_time,
            phase=phase,
            action=action,
        )
