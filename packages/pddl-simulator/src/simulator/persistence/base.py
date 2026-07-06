"""Persistence interfaces for simulator state storage."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol

from ..events import ScheduledEvent
from ..model import GroundedAction, SimulationDomain, SimulationProblem
from ..state import SimulationState
from ..trace import TraceEntry


@dataclass(frozen=True, slots=True)
class SimulationRunRecord:
    """Metadata describing one persisted simulator run."""

    run_id: int
    domain_name: str | None = None
    problem_name: str | None = None


@dataclass(frozen=True, slots=True)
class SnapshotRecord:
    """Persisted state snapshot for one simulation run."""

    snapshot_id: int
    run_id: int
    step_index: int
    sim_time: Fraction
    reason: str
    state: SimulationState
    pending_events: tuple[ScheduledEvent, ...]


@dataclass(frozen=True, slots=True)
class PlannerAttemptRecord:
    """Persisted planner-attempt metadata for one simulation run."""

    attempt_id: int
    run_id: int
    problem_name: str | None
    planner_name: str | None
    requested_timeout_seconds: float | None
    timeout_supported: bool | None
    timed_out: bool
    status: str
    failure_stage: str
    reason: str | None
    plan_topology: str | None = None


@dataclass(frozen=True, slots=True)
class ActionEventRecord:
    """Persisted structured action event."""

    event_id: int
    run_id: int
    step_index: int
    sim_time: Fraction
    phase: str
    action_name: str
    action_kind: str
    arguments: tuple[str, ...]
    duration: Fraction


class StateStore(Protocol):
    """Protocol for persisting simulator state and trace information."""

    def create_run(self, *, domain_name: str | None, problem_name: str | None) -> SimulationRunRecord:
        """Create a new persisted simulator run."""

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
        """Persist a state snapshot for the given run."""

    def append_trace_entry(self, *, run_id: int, step_index: int, entry: TraceEntry) -> None:
        """Persist one trace entry for the given run."""

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
        """Persist one planner attempt/result for the given run."""

    def persist_problem_model(
        self,
        *,
        run_id: int,
        domain: SimulationDomain,
        problem: SimulationProblem,
    ) -> None:
        """Persist static problem metadata needed to interpret trajectories."""

    def append_action_event(
        self,
        *,
        run_id: int,
        step_index: int,
        sim_time: Fraction,
        phase: str,
        action: GroundedAction,
    ) -> ActionEventRecord:
        """Persist one structured action event for the given run."""

    def load_latest_snapshot(self, run_id: int) -> SnapshotRecord | None:
        """Return the latest persisted snapshot for a run, if any."""

    def load_snapshot_at_or_before(self, run_id: int, sim_time: Fraction) -> SnapshotRecord | None:
        """Return the latest snapshot not later than ``sim_time``."""

    def iter_snapshots(
        self,
        run_id: int,
        *,
        since: Fraction | None = None,
        until: Fraction | None = None,
        stride: int | None = None,
    ) -> Iterable[SnapshotRecord]:
        """Iterate snapshots in time order, optionally filtered/strided.

        ``stride`` keeps every Nth snapshot (1 = all, 2 = every other, ...).
        Implementations may yield lazily; callers should expect a single pass.
        """
