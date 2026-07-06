"""In-memory persistence backend for parallel simulator workers."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from ..events import ScheduledEvent
from ..model import DurativeActionSchema, GroundedAction, SimulationDomain, SimulationProblem, TimedEffect
from ..state import SimulationState
from ..trace import TraceEntry
from .base import ActionEventRecord, PlannerAttemptRecord, SimulationRunRecord, SnapshotRecord, StateStore


def _noop_transition(state: SimulationState) -> None:
    return None


def _copy_state(state: SimulationState) -> SimulationState:
    return SimulationState(
        time=state.time,
        facts=set(state.facts),
        numeric_values=dict(state.numeric_values),
        running_actions=list(state.running_actions),
    )


def _copy_pending_events(events: tuple[ScheduledEvent, ...]) -> tuple[ScheduledEvent, ...]:
    # Engine-scheduled callbacks often close over action objects and lambdas,
    # which cannot be pickled across joblib workers. Persistence only needs the
    # event metadata, so replace callbacks with a module-level no-op.
    return tuple(
        ScheduledEvent(
            time=event.time,
            priority=event.priority,
            kind=event.kind,
            description=event.description,
            transition=_noop_transition,
        )
        for event in events
    )


def _copy_domain_for_persistence(domain: SimulationDomain) -> SimulationDomain:
    return SimulationDomain(
        name=domain.name,
        requirements=domain.requirements,
        types=domain.types,
        predicates=domain.predicates,
        fluents=domain.fluents,
        actions=tuple(
            DurativeActionSchema(
                name=action.name,
                action_kind=action.action_kind,
                parameters=action.parameters,
                duration=action.duration,
                duration_expression=action.duration_expression,
                start_conditions=action.start_conditions,
                overall_conditions=action.overall_conditions,
                end_conditions=action.end_conditions,
                start_effects=action.start_effects,
                end_effects=action.end_effects,
            )
            for action in domain.actions
        ),
    )


def _copy_problem_for_persistence(problem: SimulationProblem) -> SimulationProblem:
    return SimulationProblem(
        name=problem.name,
        domain_name=problem.domain_name,
        objects=problem.objects,
        initial_facts=problem.initial_facts,
        initial_numeric_values=dict(problem.initial_numeric_values),
        timed_effects=tuple(
            TimedEffect(time=effect.time, expression=effect.expression) for effect in problem.timed_effects
        ),
        goals=problem.goals,
    )


@dataclass(slots=True)
class ProblemModelRecord:
    run_id: int
    domain: SimulationDomain
    problem: SimulationProblem


@dataclass(slots=True)
class BufferedStateStore(StateStore):
    """Collect simulator persistence writes in memory.

    Parallel workers use this store so that the engine can keep calling the
    normal persistence hooks without opening the shared session database.
    The parent process later replays these records into DuckDB/SQLite in a
    deterministic order.
    """

    runs: list[SimulationRunRecord] = field(default_factory=list)
    problem_models: list[ProblemModelRecord] = field(default_factory=list)
    snapshots: list[SnapshotRecord] = field(default_factory=list)
    trace_entries: list[tuple[int, int, TraceEntry]] = field(default_factory=list)
    planner_attempts: list[PlannerAttemptRecord] = field(default_factory=list)
    action_events: list[ActionEventRecord] = field(default_factory=list)
    _next_run_id: int = 1
    _next_snapshot_id: int = 1
    _next_planner_attempt_id: int = 1
    _next_action_event_id: int = 1

    def create_run(self, *, domain_name: str | None, problem_name: str | None) -> SimulationRunRecord:
        record = SimulationRunRecord(run_id=self._next_run_id, domain_name=domain_name, problem_name=problem_name)
        self._next_run_id += 1
        self.runs.append(record)
        return record

    def save_snapshot(
        self,
        *,
        run_id: int,
        step_index: int,
        sim_time: Fraction,
        reason: str,
        state: SimulationState,
        pending_events: tuple[ScheduledEvent, ...],
    ) -> SnapshotRecord:
        record = SnapshotRecord(
            snapshot_id=self._next_snapshot_id,
            run_id=run_id,
            step_index=step_index,
            sim_time=sim_time,
            reason=reason,
            state=_copy_state(state),
            pending_events=_copy_pending_events(pending_events),
        )
        self._next_snapshot_id += 1
        self.snapshots.append(record)
        return record

    def append_trace_entry(self, *, run_id: int, step_index: int, entry: TraceEntry) -> None:
        self.trace_entries.append((run_id, step_index, entry))

    def append_planner_attempt(
        self,
        *,
        run_id: int,
        problem_name: str | None,
        planner_name: str | None,
        requested_timeout_seconds: float | None,
        timeout_supported: bool | None,
        timed_out: bool,
        status: str,
        failure_stage: str,
        reason: str | None,
        plan_topology: str | None = None,
    ) -> PlannerAttemptRecord:
        record = PlannerAttemptRecord(
            attempt_id=self._next_planner_attempt_id,
            run_id=run_id,
            problem_name=problem_name,
            planner_name=planner_name,
            requested_timeout_seconds=requested_timeout_seconds,
            timeout_supported=timeout_supported,
            timed_out=timed_out,
            status=status,
            failure_stage=failure_stage,
            reason=reason,
            plan_topology=plan_topology,
        )
        self._next_planner_attempt_id += 1
        self.planner_attempts.append(record)
        return record

    def persist_problem_model(
        self,
        *,
        run_id: int,
        domain: SimulationDomain,
        problem: SimulationProblem,
    ) -> None:
        self.problem_models.append(
            ProblemModelRecord(
                run_id=run_id,
                domain=_copy_domain_for_persistence(domain),
                problem=_copy_problem_for_persistence(problem),
            )
        )

    def append_action_event(
        self,
        *,
        run_id: int,
        step_index: int,
        sim_time: Fraction,
        phase: str,
        action: GroundedAction,
    ) -> ActionEventRecord:
        record = ActionEventRecord(
            event_id=self._next_action_event_id,
            run_id=run_id,
            step_index=step_index,
            sim_time=sim_time,
            phase=phase,
            action_name=action.name,
            action_kind=action.schema.action_kind if action.schema is not None else "unknown",
            arguments=action.arguments,
            duration=action.duration,
        )
        self._next_action_event_id += 1
        self.action_events.append(record)
        return record

    def load_latest_snapshot(self, run_id: int) -> SnapshotRecord | None:
        matches = [snapshot for snapshot in self.snapshots if snapshot.run_id == run_id]
        if not matches:
            return None
        return sorted(matches, key=lambda snapshot: (snapshot.step_index, snapshot.snapshot_id))[-1]

    def load_snapshot_at_or_before(self, run_id: int, sim_time: Fraction) -> SnapshotRecord | None:
        matches = [
            snapshot for snapshot in self.snapshots if snapshot.run_id == run_id and snapshot.sim_time <= sim_time
        ]
        if not matches:
            return None
        return sorted(matches, key=lambda snapshot: (snapshot.sim_time, snapshot.step_index, snapshot.snapshot_id))[-1]

    def iter_snapshots(
        self,
        run_id: int,
        *,
        since: Fraction | None = None,
        until: Fraction | None = None,
        stride: int | None = None,
    ):
        kept_index = 0
        for snapshot in sorted(
            (snapshot for snapshot in self.snapshots if snapshot.run_id == run_id),
            key=lambda snapshot: (snapshot.step_index, snapshot.snapshot_id),
        ):
            if since is not None and snapshot.sim_time < since:
                continue
            if until is not None and snapshot.sim_time > until:
                continue
            if stride is not None and kept_index % stride != 0:
                kept_index += 1
                continue
            kept_index += 1
            yield snapshot


def action_record_to_grounded_action(record: ActionEventRecord) -> GroundedAction:
    return GroundedAction(
        name=record.action_name,
        arguments=record.arguments,
        duration=record.duration,
        schema=DurativeActionSchema(name=record.action_name, action_kind=record.action_kind),
    )
