from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from _sailing_helpers import generate_til_problem_pddl
from simulator import FluentKey, PDDLSource, PredicateInstance, SimulatorEngine, SQLiteStateStore, UnifiedPlanningParser


def test_sqlite_state_store_persists_snapshots_over_time(tmp_path: Path) -> None:
    source = _write_problem_instance(
        tmp_path=tmp_path,
        domain_path=Path("packages/pddl-dataset/src/pddl_problem/sailing_tils/domain.pddl"),
        problem_text=generate_til_problem_pddl("til_demo", 1, [0], 1, 6),
    )
    store = SQLiteStateStore(tmp_path / "simulation.sqlite")
    engine = SimulatorEngine.from_runtime(UnifiedPlanningParser().load_runtime(source))
    engine.state_store = store
    engine.reset()

    assert engine.run_id is not None

    initial_snapshot = store.load_latest_snapshot(engine.run_id)
    assert initial_snapshot is not None
    assert initial_snapshot.reason == "reset"
    assert initial_snapshot.sim_time == Fraction(0, 1)
    assert initial_snapshot.state.holds(PredicateInstance("still_alive"))
    assert initial_snapshot.state.holds(PredicateInstance("idle", ("b0",)))
    assert initial_snapshot.state.numeric_value(FluentKey("x", ("b0",))) == Fraction(0, 1)
    assert initial_snapshot.state.numeric_value(FluentKey("y", ("b0",))) == Fraction(0, 1)
    assert not initial_snapshot.state.running_actions

    engine.start_action("go_north_east", ("b0",))

    in_flight_snapshot = store.load_latest_snapshot(engine.run_id)
    assert in_flight_snapshot is not None
    assert in_flight_snapshot.reason == "action_start"
    assert in_flight_snapshot.sim_time == Fraction(0, 1)
    assert in_flight_snapshot.state.holds(PredicateInstance("still_alive"))
    assert not in_flight_snapshot.state.holds(PredicateInstance("idle", ("b0",)))
    assert len(in_flight_snapshot.state.running_actions) == 1
    running_action = in_flight_snapshot.state.running_actions[0]
    assert running_action.name == "go_north_east"
    assert running_action.arguments == ("b0",)
    assert running_action.started_at == Fraction(0, 1)
    assert running_action.ends_at == Fraction(1, 1)
    assert any(event.kind.value == "action_end" for event in in_flight_snapshot.pending_events)
    assert any(event.kind.value == "timed_effect" for event in in_flight_snapshot.pending_events)

    engine.run_until(Fraction(1, 1))

    end_of_move_snapshot = store.load_latest_snapshot(engine.run_id)
    assert end_of_move_snapshot is not None
    assert end_of_move_snapshot.reason == "action_end"
    assert end_of_move_snapshot.sim_time == Fraction(1, 1)
    assert end_of_move_snapshot.state.holds(PredicateInstance("idle", ("b0",)))
    assert not end_of_move_snapshot.state.running_actions

    engine.run_until(Fraction(12, 1))

    snapshot_at_one = store.load_snapshot_at_or_before(engine.run_id, Fraction(1, 1))
    assert snapshot_at_one is not None
    assert snapshot_at_one.state.numeric_value(FluentKey("x", ("b0",))) == Fraction(3, 1)
    assert snapshot_at_one.state.numeric_value(FluentKey("y", ("b0",))) == Fraction(3, 1)
    assert snapshot_at_one.state.holds(PredicateInstance("still_alive"))
    assert any(event.kind.value == "timed_effect" for event in initial_snapshot.pending_events)

    final_snapshot = store.load_latest_snapshot(engine.run_id)
    assert final_snapshot is not None
    assert final_snapshot.sim_time == Fraction(12, 1)
    assert final_snapshot.state.numeric_value(FluentKey("x", ("b0",))) == Fraction(3, 1)
    assert final_snapshot.state.numeric_value(FluentKey("y", ("b0",))) == Fraction(3, 1)
    assert final_snapshot.reason == "timed_effect"
    assert not final_snapshot.state.holds(PredicateInstance("still_alive"))


def _write_problem_instance(tmp_path: Path, domain_path: Path, problem_text: str) -> PDDLSource:
    problem_path = tmp_path / "problem.pddl"
    problem_path.write_text(problem_text, encoding="utf-8")
    return PDDLSource(domain_path=domain_path, problem_path=problem_path)
