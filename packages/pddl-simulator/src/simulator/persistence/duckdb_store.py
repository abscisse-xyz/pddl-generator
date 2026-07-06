"""DuckDB-backed persistence for simulator state.

Uses native ``LIST<STRUCT(...)>`` columns instead of JSON text so analytical
queries can project individual fields without parsing — e.g.

    SELECT run_id, sim_time, len(facts) AS fact_count
    FROM state_snapshots WHERE run_id = ?
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import duckdb

from ..events import EventKind, ScheduledEvent
from ..state import FluentKey, PredicateInstance, RunningAction, SimulationState
from ..trace import TraceEntry
from .base import ActionEventRecord, PlannerAttemptRecord, SimulationRunRecord, SnapshotRecord
from .serializers import fraction_from_text, fraction_to_text


class DuckDBStateStore:
    """Persist simulator runs, snapshots, and trace entries in DuckDB."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    # ---- write side ------------------------------------------------------

    def create_run(self, *, domain_name: str | None, problem_name: str | None) -> SimulationRunRecord:
        with self._connect() as con:
            row = con.execute(
                """
                INSERT INTO simulation_runs(domain_name, problem_name, created_at)
                VALUES (?, ?, ?)
                RETURNING id
                """,
                [domain_name, problem_name, datetime.now(timezone.utc)],
            ).fetchone()
            run_id = int(row[0])
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
        facts_payload = _facts_to_payload(state.facts)
        numeric_payload = _numerics_to_payload(state.numeric_values)
        running_payload = _running_actions_to_payload(state.running_actions)
        events_payload = _pending_events_to_payload(pending_events)

        with self._connect() as con:
            row = con.execute(
                """
                INSERT INTO state_snapshots(
                    run_id, step_index, sim_time, reason,
                    facts, numeric_values, running_actions, pending_events
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                [
                    run_id,
                    step_index,
                    fraction_to_text(sim_time),
                    reason,
                    facts_payload,
                    numeric_payload,
                    running_payload,
                    events_payload,
                ],
            ).fetchone()
            snapshot_id = int(row[0])

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
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO trace_entries(run_id, step_index, sim_time, kind, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                [run_id, step_index, fraction_to_text(entry.time), entry.kind.value, entry.description],
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
        with self._connect() as con:
            row = con.execute(
                """
                INSERT INTO planner_attempts(
                    run_id, problem_name, planner_name, requested_timeout_seconds,
                    timeout_supported, timed_out, status, failure_stage, reason, plan_topology, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                [
                    run_id,
                    problem_name,
                    planner_name,
                    requested_timeout_seconds,
                    timeout_supported,
                    timed_out,
                    status,
                    failure_stage,
                    reason,
                    plan_topology,
                    datetime.now(timezone.utc),
                ],
            ).fetchone()
            attempt_id = int(row[0])
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
        with self._connect() as con:
            con.execute("DELETE FROM problem_objects WHERE run_id = ?", [run_id])
            con.execute("DELETE FROM predicate_symbols WHERE run_id = ?", [run_id])
            con.execute("DELETE FROM fluent_symbols WHERE run_id = ?", [run_id])
            con.execute("DELETE FROM action_schemas WHERE run_id = ?", [run_id])
            con.execute("DELETE FROM problem_goals WHERE run_id = ?", [run_id])
            con.execute("DELETE FROM problem_timed_effects WHERE run_id = ?", [run_id])

            if problem.objects:
                con.executemany(
                    """
                    INSERT INTO problem_objects(run_id, object_name, type_name)
                    VALUES (?, ?, ?)
                    """,
                    [(run_id, obj.name, obj.type_name) for obj in problem.objects],
                )
            if domain.predicates:
                con.executemany(
                    """
                    INSERT INTO predicate_symbols(run_id, predicate_name, parameter_types)
                    VALUES (?, ?, ?)
                    """,
                    [(run_id, predicate.name, list(predicate.parameter_types)) for predicate in domain.predicates],
                )
            if domain.fluents:
                con.executemany(
                    """
                    INSERT INTO fluent_symbols(run_id, fluent_name, parameter_types)
                    VALUES (?, ?, ?)
                    """,
                    [(run_id, fluent.name, list(fluent.parameter_types)) for fluent in domain.fluents],
                )
            if domain.actions:
                con.executemany(
                    """
                    INSERT INTO action_schemas(
                        run_id, action_name, action_kind, parameter_names, parameter_types,
                        duration, duration_expression, start_conditions, overall_conditions,
                        end_conditions, start_effects, end_effects
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            run_id,
                            action.name,
                            action.action_kind,
                            [parameter.name for parameter in action.parameters],
                            [parameter.type_name for parameter in action.parameters],
                            fraction_to_text(action.duration),
                            action.duration_expression,
                            list(action.start_conditions),
                            list(action.overall_conditions),
                            list(action.end_conditions),
                            list(action.start_effects),
                            list(action.end_effects),
                        )
                        for action in domain.actions
                    ],
                )
            if problem.goals:
                con.executemany(
                    """
                    INSERT INTO problem_goals(run_id, goal_index, expression)
                    VALUES (?, ?, ?)
                    """,
                    [(run_id, index, goal) for index, goal in enumerate(problem.goals)],
                )
            if problem.timed_effects:
                con.executemany(
                    """
                    INSERT INTO problem_timed_effects(run_id, effect_index, effect_time, expression)
                    VALUES (?, ?, ?, ?)
                    """,
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
        with self._connect() as con:
            row = con.execute(
                """
                INSERT INTO action_events(
                    run_id, step_index, sim_time, phase, action_name, action_kind,
                    arguments, duration
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                [
                    run_id,
                    step_index,
                    fraction_to_text(sim_time),
                    phase,
                    action.name,
                    action.schema.action_kind if action.schema is not None else "unknown",
                    list(action.arguments),
                    fraction_to_text(action.duration),
                ],
            ).fetchone()
            event_id = int(row[0])
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

    # ---- read side -------------------------------------------------------

    def load_latest_snapshot(self, run_id: int) -> SnapshotRecord | None:
        with self._connect() as con:
            row = con.execute(
                f"""
                SELECT {_SNAPSHOT_COLUMNS}
                FROM state_snapshots
                WHERE run_id = ?
                ORDER BY step_index DESC, id DESC
                LIMIT 1
                """,
                [run_id],
            ).fetchone()
        return _row_to_snapshot(row)

    def load_snapshot_at_or_before(self, run_id: int, sim_time: Fraction) -> SnapshotRecord | None:
        target = fraction_to_text(sim_time)
        with self._connect() as con:
            rows = con.execute(
                f"""
                SELECT {_SNAPSHOT_COLUMNS}
                FROM state_snapshots
                WHERE run_id = ?
                ORDER BY step_index ASC, id ASC
                """,
                [run_id],
            ).fetchall()
        candidates = [_row_to_snapshot(row) for row in rows]
        candidates = [snap for snap in candidates if snap is not None and snap.sim_time <= sim_time]
        return candidates[-1] if candidates else None

    def iter_snapshots(
        self,
        run_id: int,
        *,
        since: Fraction | None = None,
        until: Fraction | None = None,
        stride: int | None = None,
    ) -> Iterator[SnapshotRecord]:
        """Yield snapshots in time order, optionally filtered by sim_time and strided.

        ``stride`` keeps every Nth snapshot (1 = all, 2 = every other, …).
        """
        with self._connect() as con:
            rows = con.execute(
                f"""
                SELECT {_SNAPSHOT_COLUMNS}
                FROM state_snapshots
                WHERE run_id = ?
                ORDER BY step_index ASC, id ASC
                """,
                [run_id],
            ).fetchall()
        snapshots = [_row_to_snapshot(row) for row in rows]
        for index, snapshot in enumerate(snap for snap in snapshots if snap is not None):
            if stride is not None and index % stride != 0:
                continue
            if since is not None and snapshot.sim_time < since:
                continue
            if until is not None and snapshot.sim_time > until:
                continue
            yield snapshot

    # ---- export ----------------------------------------------------------

    def export_parquet(self, run_id: int, out_dir: str | Path) -> tuple[Path, Path]:
        """Export this run's snapshots and trace entries to Parquet files.

        Returns the (snapshots_path, trace_path) actually written.
        """
        out_dir_path = Path(out_dir)
        out_dir_path.mkdir(parents=True, exist_ok=True)
        snapshots_path = out_dir_path / "snapshots.parquet"
        trace_path = out_dir_path / "trace.parquet"

        # DuckDB's COPY ... TO does not accept a parameterized path; escape the
        # quoted literal to keep this safe against unusual path characters.
        snapshots_target = str(snapshots_path).replace("'", "''")
        trace_target = str(trace_path).replace("'", "''")
        with self._connect() as con:
            con.execute(
                f"""
                COPY (SELECT * FROM state_snapshots WHERE run_id = ? ORDER BY step_index, id)
                TO '{snapshots_target}' (FORMAT PARQUET)
                """,
                [run_id],
            )
            con.execute(
                f"""
                COPY (SELECT * FROM trace_entries WHERE run_id = ? ORDER BY step_index, id)
                TO '{trace_target}' (FORMAT PARQUET)
                """,
                [run_id],
            )
        return snapshots_path, trace_path

    # ---- internals -------------------------------------------------------

    def _connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.database_path))

    def _initialize_schema(self) -> None:
        with self._connect() as con:
            con.execute("CREATE SEQUENCE IF NOT EXISTS seq_runs START 1")
            con.execute("CREATE SEQUENCE IF NOT EXISTS seq_snapshots START 1")
            con.execute("CREATE SEQUENCE IF NOT EXISTS seq_trace START 1")
            con.execute("CREATE SEQUENCE IF NOT EXISTS seq_planner_attempts START 1")
            con.execute("CREATE SEQUENCE IF NOT EXISTS seq_action_events START 1")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    id BIGINT PRIMARY KEY DEFAULT nextval('seq_runs'),
                    domain_name VARCHAR,
                    problem_name VARCHAR,
                    created_at TIMESTAMP NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS state_snapshots (
                    id BIGINT PRIMARY KEY DEFAULT nextval('seq_snapshots'),
                    run_id BIGINT NOT NULL,
                    step_index INTEGER NOT NULL,
                    sim_time VARCHAR NOT NULL,
                    reason VARCHAR NOT NULL,
                    facts STRUCT(name VARCHAR, arguments VARCHAR[])[],
                    numeric_values STRUCT(name VARCHAR, arguments VARCHAR[], value VARCHAR)[],
                    running_actions STRUCT(name VARCHAR, arguments VARCHAR[], started_at VARCHAR, ends_at VARCHAR)[],
                    pending_events STRUCT("time" VARCHAR, priority INTEGER, kind VARCHAR, description VARCHAR)[]
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_run_step ON state_snapshots(run_id, step_index)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS trace_entries (
                    id BIGINT PRIMARY KEY DEFAULT nextval('seq_trace'),
                    run_id BIGINT NOT NULL,
                    step_index INTEGER NOT NULL,
                    sim_time VARCHAR NOT NULL,
                    kind VARCHAR NOT NULL,
                    description VARCHAR NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_trace_run_step ON trace_entries(run_id, step_index)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS planner_attempts (
                    id BIGINT PRIMARY KEY DEFAULT nextval('seq_planner_attempts'),
                    run_id BIGINT NOT NULL,
                    problem_name VARCHAR,
                    planner_name VARCHAR,
                    requested_timeout_seconds DOUBLE,
                    timeout_supported BOOLEAN,
                    timed_out BOOLEAN NOT NULL,
                    status VARCHAR NOT NULL,
                    failure_stage VARCHAR NOT NULL,
                    reason VARCHAR,
                    plan_topology VARCHAR,
                    created_at TIMESTAMP NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_planner_attempts_run_id ON planner_attempts(run_id)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS problem_objects (
                    run_id BIGINT NOT NULL,
                    object_name VARCHAR NOT NULL,
                    type_name VARCHAR NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_problem_objects_run_id ON problem_objects(run_id)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS predicate_symbols (
                    run_id BIGINT NOT NULL,
                    predicate_name VARCHAR NOT NULL,
                    parameter_types VARCHAR[]
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_predicate_symbols_run_id ON predicate_symbols(run_id)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS fluent_symbols (
                    run_id BIGINT NOT NULL,
                    fluent_name VARCHAR NOT NULL,
                    parameter_types VARCHAR[]
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_fluent_symbols_run_id ON fluent_symbols(run_id)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS action_schemas (
                    run_id BIGINT NOT NULL,
                    action_name VARCHAR NOT NULL,
                    action_kind VARCHAR NOT NULL,
                    parameter_names VARCHAR[],
                    parameter_types VARCHAR[],
                    duration VARCHAR NOT NULL,
                    duration_expression VARCHAR NOT NULL,
                    start_conditions VARCHAR[],
                    overall_conditions VARCHAR[],
                    end_conditions VARCHAR[],
                    start_effects VARCHAR[],
                    end_effects VARCHAR[]
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_action_schemas_run_id ON action_schemas(run_id)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS problem_goals (
                    run_id BIGINT NOT NULL,
                    goal_index INTEGER NOT NULL,
                    expression VARCHAR NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_problem_goals_run_id ON problem_goals(run_id)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS problem_timed_effects (
                    run_id BIGINT NOT NULL,
                    effect_index INTEGER NOT NULL,
                    effect_time VARCHAR NOT NULL,
                    expression VARCHAR NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_problem_timed_effects_run_id ON problem_timed_effects(run_id)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS action_events (
                    id BIGINT PRIMARY KEY DEFAULT nextval('seq_action_events'),
                    run_id BIGINT NOT NULL,
                    step_index INTEGER NOT NULL,
                    sim_time VARCHAR NOT NULL,
                    phase VARCHAR NOT NULL,
                    action_name VARCHAR NOT NULL,
                    action_kind VARCHAR NOT NULL,
                    arguments VARCHAR[],
                    duration VARCHAR NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_action_events_run_step ON action_events(run_id, step_index)")
            con.execute(
                """
                CREATE VIEW IF NOT EXISTS state_action_transitions AS
                SELECT
                    action.run_id,
                    action.step_index,
                    action.sim_time,
                    action.phase,
                    action.action_name,
                    action.action_kind,
                    action.arguments,
                    action.duration,
                    before.facts AS state_facts,
                    before.numeric_values AS state_numeric_values,
                    before.running_actions AS state_running_actions,
                    after.facts AS next_state_facts,
                    after.numeric_values AS next_state_numeric_values,
                    after.running_actions AS next_state_running_actions
                FROM action_events action
                JOIN state_snapshots after
                  ON after.run_id = action.run_id
                 AND after.step_index = action.step_index
                LEFT JOIN state_snapshots before
                  ON before.run_id = action.run_id
                 AND before.step_index = action.step_index - 1
                """
            )


# ---- payload helpers (module-level so they can be reused) ----------------

_SNAPSHOT_COLUMNS = "id, run_id, step_index, sim_time, reason, facts, numeric_values, running_actions, pending_events"


def _facts_to_payload(facts: Iterable[PredicateInstance]) -> list[dict]:
    return [
        {"name": f.name, "arguments": list(f.arguments)} for f in sorted(facts, key=lambda x: (x.name, x.arguments))
    ]


def _numerics_to_payload(values: dict[FluentKey, Fraction]) -> list[dict]:
    return [
        {"name": k.name, "arguments": list(k.arguments), "value": fraction_to_text(v)}
        for k, v in sorted(values.items(), key=lambda kv: (kv[0].name, kv[0].arguments))
    ]


def _running_actions_to_payload(actions: list[RunningAction]) -> list[dict]:
    return [
        {
            "name": a.name,
            "arguments": list(a.arguments),
            "started_at": fraction_to_text(a.started_at),
            "ends_at": fraction_to_text(a.ends_at),
        }
        for a in sorted(actions, key=lambda x: (x.started_at, x.name, x.arguments))
    ]


def _pending_events_to_payload(events: tuple[ScheduledEvent, ...]) -> list[dict]:
    return [
        {"time": fraction_to_text(e.time), "priority": e.priority, "kind": e.kind.value, "description": e.description}
        for e in sorted(events, key=lambda x: (x.time, x.priority, x.kind.value, x.description))
    ]


def _row_to_snapshot(row) -> SnapshotRecord | None:
    if row is None:
        return None
    snapshot_id, run_id, step_index, sim_time_text, reason, facts, numeric_values, running_actions, pending_events = row
    sim_time = fraction_from_text(sim_time_text)

    state = SimulationState(time=sim_time)
    for fact in facts or []:
        state.set_fact(PredicateInstance(name=fact["name"], arguments=tuple(fact["arguments"])), True)
    for entry in numeric_values or []:
        state.set_numeric_value(
            FluentKey(name=entry["name"], arguments=tuple(entry["arguments"])),
            fraction_from_text(entry["value"]),
        )
    state.running_actions = [
        RunningAction(
            name=entry["name"],
            arguments=tuple(entry["arguments"]),
            started_at=fraction_from_text(entry["started_at"]),
            ends_at=fraction_from_text(entry["ends_at"]),
        )
        for entry in running_actions or []
    ]

    events = tuple(
        ScheduledEvent(
            time=fraction_from_text(entry["time"]),
            priority=int(entry["priority"]),
            kind=EventKind(entry["kind"]),
            description=entry["description"],
            transition=lambda state: None,  # transitions are not persisted
        )
        for entry in pending_events or []
    )

    return SnapshotRecord(
        snapshot_id=int(snapshot_id),
        run_id=int(run_id),
        step_index=int(step_index),
        sim_time=sim_time,
        reason=reason,
        state=state,
        pending_events=events,
    )
