"""Tests for the DuckDB-backed state store.

These mirror the SQLite tests' shape but exercise the native LIST<STRUCT> path,
plus the new `iter_snapshots` and `export_parquet` capabilities.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import duckdb
from _sailing_helpers import generate_til_problem_pddl
from simulator import (
    DuckDBStateStore,
    FluentKey,
    PDDLSource,
    PredicateInstance,
    SimulatorEngine,
    UnifiedPlanningParser,
)

_TRAVEL_PROBLEM_PDDL = """(define (problem travel_demo)
 (:domain travel_domain)
 (:objects
    l1 l2 l3 - location
 )
 (:init
    (is_at l1)
    (= (total_travel_time) 0)
    (is_connected l1 l2)
    (= (travel_time l1 l2) 3)
    (is_connected l2 l3)
    (= (travel_time l2 l3) 5)
 )
 (:goal (and
    (is_at l3)
 ))
 (:metric minimize (total_travel_time))
)
"""


def _write_problem_instance(*, tmp_path: Path, domain_path: Path, problem_text: str) -> PDDLSource:
    target_problem = tmp_path / "problem.pddl"
    target_domain = tmp_path / "domain.pddl"
    target_problem.write_text(problem_text)
    target_domain.write_text(domain_path.read_text())
    return PDDLSource(domain_path=target_domain, problem_path=target_problem)


def _make_engine_and_store(tmp_path: Path) -> tuple[SimulatorEngine, DuckDBStateStore]:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )
    store = DuckDBStateStore(tmp_path / "simulation.duckdb")
    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))
    engine.state_store = store
    engine.reset()
    return engine, store


def test_duckdb_store_persists_initial_snapshot(tmp_path: Path) -> None:
    engine, store = _make_engine_and_store(tmp_path)
    assert engine.run_id is not None

    initial = store.load_latest_snapshot(engine.run_id)
    assert initial is not None
    assert initial.reason == "reset"
    assert initial.sim_time == Fraction(0, 1)
    assert initial.state.holds(PredicateInstance("still_alive"))
    assert initial.state.holds(PredicateInstance("idle", ("b0",)))
    assert initial.state.numeric_value(FluentKey("x", ("b0",))) == Fraction(0, 1)


def test_duckdb_store_records_action_lifecycle(tmp_path: Path) -> None:
    engine, store = _make_engine_and_store(tmp_path)
    engine.start_action("go_north_east", ("b0",))

    in_flight = store.load_latest_snapshot(engine.run_id)
    assert in_flight is not None
    assert in_flight.reason == "action_start"
    assert not in_flight.state.holds(PredicateInstance("idle", ("b0",)))
    assert in_flight.state.running_actions
    assert in_flight.state.running_actions[0].name == "go_north_east"


def test_duckdb_store_at_or_before_returns_correct_snapshot(tmp_path: Path) -> None:
    engine, store = _make_engine_and_store(tmp_path)
    engine.start_action("go_north_east", ("b0",))
    engine.run_until(Fraction(1, 1))
    engine.start_action("go_north_west", ("b0",))
    engine.run_until(Fraction(2, 1))

    snap_at_half = store.load_snapshot_at_or_before(engine.run_id, Fraction(1, 2))
    assert snap_at_half is not None
    assert snap_at_half.sim_time <= Fraction(1, 2)

    snap_at_three_halves = store.load_snapshot_at_or_before(engine.run_id, Fraction(3, 2))
    assert snap_at_three_halves is not None
    assert Fraction(1, 1) <= snap_at_three_halves.sim_time <= Fraction(3, 2)


def test_duckdb_store_iter_snapshots_orders_and_strides(tmp_path: Path) -> None:
    engine, store = _make_engine_and_store(tmp_path)
    engine.start_action("go_north_east", ("b0",))
    engine.run_until(Fraction(1, 1))
    engine.start_action("go_north_west", ("b0",))
    engine.run_until(Fraction(2, 1))

    all_snapshots = list(store.iter_snapshots(engine.run_id))
    assert len(all_snapshots) >= 4
    times = [snap.sim_time for snap in all_snapshots]
    assert times == sorted(times)

    every_other = list(store.iter_snapshots(engine.run_id, stride=2))
    assert len(every_other) == (len(all_snapshots) + 1) // 2

    after_one = list(store.iter_snapshots(engine.run_id, since=Fraction(1, 1)))
    assert all(snap.sim_time >= Fraction(1, 1) for snap in after_one)


def test_duckdb_store_exports_parquet_files(tmp_path: Path) -> None:
    engine, store = _make_engine_and_store(tmp_path)
    engine.start_action("go_north_east", ("b0",))
    engine.run_until(Fraction(1, 1))

    out_dir = tmp_path / "parquet_out"
    snapshots_path, trace_path = store.export_parquet(engine.run_id, out_dir)

    assert snapshots_path.exists()
    assert trace_path.exists()

    # Round-trip via a separate connection — proves the file is portable.
    with duckdb.connect(":memory:") as con:
        snapshot_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{snapshots_path}')").fetchone()[0]
        trace_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{trace_path}')").fetchone()[0]
    assert snapshot_count >= 2
    assert trace_count >= 1


def test_duckdb_store_native_columns_are_queryable_without_json_parsing(tmp_path: Path) -> None:
    """Confirm the native LIST<STRUCT> shape works for analytical queries."""
    engine, store = _make_engine_and_store(tmp_path)
    engine.start_action("go_north_east", ("b0",))
    engine.run_until(Fraction(1, 1))

    with duckdb.connect(str(store.database_path)) as con:
        rows = con.execute(
            """
            SELECT step_index, len(facts) AS fact_count, len(running_actions) AS running_count
            FROM state_snapshots
            WHERE run_id = ?
            ORDER BY step_index
            """,
            [engine.run_id],
        ).fetchall()
    assert rows
    # At least one snapshot has a non-empty fact set.
    assert any(fact_count > 0 for _, fact_count, _ in rows)


def test_duckdb_store_records_planner_attempts(tmp_path: Path) -> None:
    engine, store = _make_engine_and_store(tmp_path)
    assert engine.run_id is not None

    attempt = store.append_planner_attempt(
        run_id=engine.run_id,
        problem_name="til_demo",
        planner_name="enhsp",
        requested_timeout_seconds=5.0,
        timeout_supported=True,
        timed_out=True,
        status="TIMEOUT",
        failure_stage="plan",
        reason="Planner timed out.",
        plan_topology=None,
    )

    assert attempt.run_id == engine.run_id
    assert attempt.status == "TIMEOUT"

    with duckdb.connect(str(store.database_path)) as con:
        row = con.execute(
            """
            SELECT problem_name, planner_name, requested_timeout_seconds, timeout_supported,
                   timed_out, status, failure_stage, reason
            FROM planner_attempts
            WHERE run_id = ?
            """,
            [engine.run_id],
        ).fetchone()
    assert row == ("til_demo", "enhsp", 5.0, True, True, "TIMEOUT", "plan", "Planner timed out.")


def test_duckdb_store_persists_static_model_and_action_trajectory(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/travel/domain.pddl"),
        problem_text=_TRAVEL_PROBLEM_PDDL,
    )
    store = DuckDBStateStore(tmp_path / "simulation.duckdb")
    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))
    engine.state_store = store
    engine.reset()
    assert engine.run_id is not None

    engine.start_action("move", ("l1", "l2"))
    engine.start_action("move", ("l2", "l3"))

    with duckdb.connect(str(store.database_path)) as con:
        object_count = con.execute(
            "SELECT COUNT(*) FROM problem_objects WHERE run_id = ?",
            [engine.run_id],
        ).fetchone()[0]
        action_events = con.execute(
            """
            SELECT step_index, phase, action_name, action_kind, arguments
            FROM action_events
            WHERE run_id = ?
            ORDER BY step_index
            """,
            [engine.run_id],
        ).fetchall()
        snapshots = con.execute(
            """
            SELECT step_index, reason, facts, numeric_values
            FROM state_snapshots
            WHERE run_id = ?
            ORDER BY step_index
            """,
            [engine.run_id],
        ).fetchall()
        transitions = con.execute(
            """
            SELECT step_index, action_name, arguments, state_facts, next_state_facts
            FROM state_action_transitions
            WHERE run_id = ?
            ORDER BY step_index
            """,
            [engine.run_id],
        ).fetchall()

    assert object_count == 3
    assert action_events == [
        (1, "apply", "move", "instantaneous", ["l1", "l2"]),
        (2, "apply", "move", "instantaneous", ["l2", "l3"]),
    ]
    assert snapshots[0][1] == "reset"
    assert snapshots[1][1] == "action_apply"
    assert snapshots[2][1] == "action_apply"
    assert [row[1:3] for row in transitions] == [
        ("move", ["l1", "l2"]),
        ("move", ["l2", "l3"]),
    ]
    assert any(fact["name"] == "is_at" and fact["arguments"] == ["l1"] for fact in transitions[0][3])
    assert any(fact["name"] == "is_at" and fact["arguments"] == ["l2"] for fact in transitions[0][4])
