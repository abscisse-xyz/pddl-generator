"""SQLite-backed persistence for simulator state."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

from .base import ActionEventRecord, PlannerAttemptRecord, SimulationRunRecord, SnapshotRecord
from .serializers import (
    deserialize_pending_events,
    deserialize_state,
    fraction_from_text,
    fraction_to_text,
    serialize_pending_events,
    serialize_state,
)
from ..events import ScheduledEvent
from ..state import SimulationState
from ..trace import TraceEntry


class SQLiteStateStore:
    """Persist simulator runs, snapshots, and trace entries in SQLite."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def create_run(self, *, domain_name: str | None, problem_name: str | None) -> SimulationRunRecord:
        """Create a new persisted run row."""

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO simulation_runs(domain_name, problem_name, created_at)
                VALUES (?, ?, ?)
                """,
                (domain_name, problem_name, datetime.now(timezone.utc).isoformat()),
            )
            run_id = int(cursor.lastrowid)
        return SimulationRunRecord(run_id=run_id, domain_name=domain_name, problem_name=problem_name)

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
        """Persist one state snapshot."""

        facts_json, numeric_values_json, running_actions_json = serialize_state(state)
        pending_events_json = serialize_pending_events(pending_events)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO state_snapshots(
                    run_id,
                    step_index,
                    sim_time,
                    reason,
                    facts_json,
                    numeric_values_json,
                    running_actions_json,
                    pending_events_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    step_index,
                    fraction_to_text(sim_time),
                    reason,
                    facts_json,
                    numeric_values_json,
                    running_actions_json,
                    pending_events_json,
                ),
            )
            snapshot_id = int(cursor.lastrowid)
        return SnapshotRecord(
            snapshot_id=snapshot_id,
            run_id=run_id,
            step_index=step_index,
            sim_time=sim_time,
            reason=reason,
            state=state,
            pending_events=pending_events,
        )

    def append_trace_entry(self, *, run_id: int, step_index: int, entry: TraceEntry) -> None:
        """Persist one trace entry."""

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO trace_entries(run_id, step_index, sim_time, kind, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, step_index, fraction_to_text(entry.time), entry.kind.value, entry.description),
            )

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
        """Persist one planner attempt/result."""

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO planner_attempts(
                    run_id, problem_name, planner_name, requested_timeout_seconds,
                    timeout_supported, timed_out, status, failure_stage, reason, plan_topology, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    problem_name,
                    planner_name,
                    requested_timeout_seconds,
                    timeout_supported,
                    int(timed_out),
                    status,
                    failure_stage,
                    reason,
                    plan_topology,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            attempt_id = int(cursor.lastrowid)
        return PlannerAttemptRecord(
            attempt_id=attempt_id,
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

    def persist_problem_model(
        self,
        *,
        run_id: int,
        domain,
        problem,
    ) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM problem_objects WHERE run_id = ?", (run_id,))
            connection.execute("DELETE FROM predicate_symbols WHERE run_id = ?", (run_id,))
            connection.execute("DELETE FROM fluent_symbols WHERE run_id = ?", (run_id,))
            connection.execute("DELETE FROM action_schemas WHERE run_id = ?", (run_id,))
            connection.execute("DELETE FROM problem_goals WHERE run_id = ?", (run_id,))
            connection.execute("DELETE FROM problem_timed_effects WHERE run_id = ?", (run_id,))

            connection.executemany(
                "INSERT INTO problem_objects(run_id, object_name, type_name) VALUES (?, ?, ?)",
                [(run_id, obj.name, obj.type_name) for obj in problem.objects],
            )
            connection.executemany(
                "INSERT INTO predicate_symbols(run_id, predicate_name, parameter_types_json) VALUES (?, ?, ?)",
                [
                    (run_id, predicate.name, json.dumps(list(predicate.parameter_types)))
                    for predicate in domain.predicates
                ],
            )
            connection.executemany(
                "INSERT INTO fluent_symbols(run_id, fluent_name, parameter_types_json) VALUES (?, ?, ?)",
                [(run_id, fluent.name, json.dumps(list(fluent.parameter_types))) for fluent in domain.fluents],
            )
            connection.executemany(
                """
                INSERT INTO action_schemas(
                    run_id, action_name, action_kind, parameter_names_json, parameter_types_json,
                    duration, duration_expression, start_conditions_json, overall_conditions_json,
                    end_conditions_json, start_effects_json, end_effects_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        action.name,
                        action.action_kind,
                        json.dumps([parameter.name for parameter in action.parameters]),
                        json.dumps([parameter.type_name for parameter in action.parameters]),
                        fraction_to_text(action.duration),
                        action.duration_expression,
                        json.dumps(list(action.start_conditions)),
                        json.dumps(list(action.overall_conditions)),
                        json.dumps(list(action.end_conditions)),
                        json.dumps(list(action.start_effects)),
                        json.dumps(list(action.end_effects)),
                    )
                    for action in domain.actions
                ],
            )
            connection.executemany(
                "INSERT INTO problem_goals(run_id, goal_index, expression) VALUES (?, ?, ?)",
                [(run_id, index, goal) for index, goal in enumerate(problem.goals)],
            )
            connection.executemany(
                "INSERT INTO problem_timed_effects(run_id, effect_index, effect_time, expression) VALUES (?, ?, ?, ?)",
                [
                    (run_id, index, fraction_to_text(effect.time), effect.expression)
                    for index, effect in enumerate(problem.timed_effects)
                ],
            )

    def append_action_event(
        self,
        *,
        run_id: int,
        step_index: int,
        sim_time: Fraction,
        phase: str,
        action,
    ) -> ActionEventRecord:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO action_events(
                    run_id, step_index, sim_time, phase, action_name, action_kind,
                    arguments_json, duration
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    step_index,
                    fraction_to_text(sim_time),
                    phase,
                    action.name,
                    action.schema.action_kind if action.schema is not None else "unknown",
                    json.dumps(list(action.arguments)),
                    fraction_to_text(action.duration),
                ),
            )
            event_id = int(cursor.lastrowid)
        return ActionEventRecord(
            event_id=event_id,
            run_id=run_id,
            step_index=step_index,
            sim_time=sim_time,
            phase=phase,
            action_name=action.name,
            action_kind=action.schema.action_kind if action.schema is not None else "unknown",
            arguments=action.arguments,
            duration=action.duration,
        )

    def load_latest_snapshot(self, run_id: int) -> SnapshotRecord | None:
        """Return the latest snapshot for the given run."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, run_id, step_index, sim_time, reason,
                       facts_json, numeric_values_json, running_actions_json, pending_events_json
                FROM state_snapshots
                WHERE run_id = ?
                ORDER BY step_index DESC, id DESC
                LIMIT 1
                """,
                (run_id,),
            ).fetchone()
        return self._row_to_snapshot(row)

    def iter_snapshots(
        self,
        run_id: int,
        *,
        since: Fraction | None = None,
        until: Fraction | None = None,
        stride: int | None = None,
    ):
        """Iterate snapshots in time order with optional sim_time / stride filters."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, run_id, step_index, sim_time, reason,
                       facts_json, numeric_values_json, running_actions_json, pending_events_json
                FROM state_snapshots
                WHERE run_id = ?
                ORDER BY step_index ASC, id ASC
                """,
                (run_id,),
            ).fetchall()
        kept_index = 0
        for row in rows:
            snapshot = self._row_to_snapshot(row)
            if snapshot is None:
                continue
            if since is not None and snapshot.sim_time < since:
                continue
            if until is not None and snapshot.sim_time > until:
                continue
            if stride is not None and kept_index % stride != 0:
                kept_index += 1
                continue
            kept_index += 1
            yield snapshot

    def load_snapshot_at_or_before(self, run_id: int, sim_time: Fraction) -> SnapshotRecord | None:
        """Return the latest snapshot with ``sim_time`` not greater than the request."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, run_id, step_index, sim_time, reason,
                       facts_json, numeric_values_json, running_actions_json, pending_events_json
                FROM state_snapshots
                WHERE run_id = ?
                ORDER BY step_index ASC, id ASC
                """,
                (run_id,),
            ).fetchall()
        candidates = [self._row_to_snapshot(row) for row in rows]
        candidates = [snapshot for snapshot in candidates if snapshot is not None and snapshot.sim_time <= sim_time]
        if not candidates:
            return None
        return candidates[-1]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_name TEXT,
                    problem_name TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS state_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    step_index INTEGER NOT NULL,
                    sim_time TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    facts_json TEXT NOT NULL,
                    numeric_values_json TEXT NOT NULL,
                    running_actions_json TEXT NOT NULL,
                    pending_events_json TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES simulation_runs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_state_snapshots_run_step
                ON state_snapshots(run_id, step_index);

                CREATE TABLE IF NOT EXISTS trace_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    step_index INTEGER NOT NULL,
                    sim_time TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    description TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES simulation_runs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_trace_entries_run_step
                ON trace_entries(run_id, step_index);

                CREATE TABLE IF NOT EXISTS planner_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    problem_name TEXT,
                    planner_name TEXT,
                    requested_timeout_seconds REAL,
                    timeout_supported INTEGER,
                    timed_out INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    failure_stage TEXT NOT NULL,
                    reason TEXT,
                    plan_topology TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES simulation_runs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_planner_attempts_run_id
                ON planner_attempts(run_id);

                CREATE TABLE IF NOT EXISTS problem_objects (
                    run_id INTEGER NOT NULL,
                    object_name TEXT NOT NULL,
                    type_name TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES simulation_runs(id)
                );

                CREATE TABLE IF NOT EXISTS predicate_symbols (
                    run_id INTEGER NOT NULL,
                    predicate_name TEXT NOT NULL,
                    parameter_types_json TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES simulation_runs(id)
                );

                CREATE TABLE IF NOT EXISTS fluent_symbols (
                    run_id INTEGER NOT NULL,
                    fluent_name TEXT NOT NULL,
                    parameter_types_json TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES simulation_runs(id)
                );

                CREATE TABLE IF NOT EXISTS action_schemas (
                    run_id INTEGER NOT NULL,
                    action_name TEXT NOT NULL,
                    action_kind TEXT NOT NULL,
                    parameter_names_json TEXT NOT NULL,
                    parameter_types_json TEXT NOT NULL,
                    duration TEXT NOT NULL,
                    duration_expression TEXT NOT NULL,
                    start_conditions_json TEXT NOT NULL,
                    overall_conditions_json TEXT NOT NULL,
                    end_conditions_json TEXT NOT NULL,
                    start_effects_json TEXT NOT NULL,
                    end_effects_json TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES simulation_runs(id)
                );

                CREATE TABLE IF NOT EXISTS problem_goals (
                    run_id INTEGER NOT NULL,
                    goal_index INTEGER NOT NULL,
                    expression TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES simulation_runs(id)
                );

                CREATE TABLE IF NOT EXISTS problem_timed_effects (
                    run_id INTEGER NOT NULL,
                    effect_index INTEGER NOT NULL,
                    effect_time TEXT NOT NULL,
                    expression TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES simulation_runs(id)
                );

                CREATE TABLE IF NOT EXISTS action_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    step_index INTEGER NOT NULL,
                    sim_time TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    action_kind TEXT NOT NULL,
                    arguments_json TEXT NOT NULL,
                    duration TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES simulation_runs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_action_events_run_step
                ON action_events(run_id, step_index);

                CREATE VIEW IF NOT EXISTS state_action_transitions AS
                SELECT
                    action.run_id,
                    action.step_index,
                    action.sim_time,
                    action.phase,
                    action.action_name,
                    action.action_kind,
                    action.arguments_json,
                    action.duration,
                    before.facts_json AS state_facts_json,
                    before.numeric_values_json AS state_numeric_values_json,
                    before.running_actions_json AS state_running_actions_json,
                    after.facts_json AS next_state_facts_json,
                    after.numeric_values_json AS next_state_numeric_values_json,
                    after.running_actions_json AS next_state_running_actions_json
                FROM action_events action
                JOIN state_snapshots after
                  ON after.run_id = action.run_id
                 AND after.step_index = action.step_index
                LEFT JOIN state_snapshots before
                  ON before.run_id = action.run_id
                 AND before.step_index = action.step_index - 1;
                """
            )

    def _row_to_snapshot(self, row: sqlite3.Row | None) -> SnapshotRecord | None:
        if row is None:
            return None
        sim_time = fraction_from_text(row["sim_time"])
        state = deserialize_state(
            sim_time=sim_time,
            facts_json=row["facts_json"],
            numeric_values_json=row["numeric_values_json"],
            running_actions_json=row["running_actions_json"],
        )
        pending_events = deserialize_pending_events(row["pending_events_json"])
        return SnapshotRecord(
            snapshot_id=int(row["id"]),
            run_id=int(row["run_id"]),
            step_index=int(row["step_index"]),
            sim_time=sim_time,
            reason=row["reason"],
            state=state,
            pending_events=pending_events,
        )
