"""End-to-end tests for `simulator.simulate_cli`.

We use a tiny single-action temporal domain so the test depends only on the
default `OneshotPlanner` returning a plan, not on a particular planner being
available. Tests skip if no UP planner can be invoked in the environment.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from simulator import simulate_cli
from simulator.simulate_cli import _PlanningOutcome
from simulator.simulate_cli import main as simulate_main
from unified_planning.engines.results import PlanGenerationResultStatus
from unified_planning.plans import ActionInstance, SequentialPlan

_DOMAIN_PDDL = """(define (domain simple-temporal)
  (:requirements :typing :durative-actions)
  (:types loc)
  (:predicates (at ?l - loc) (connected ?from - loc ?to - loc))
  (:durative-action move
    :parameters (?from - loc ?to - loc)
    :duration (= ?duration 1)
    :condition (and (at start (at ?from)) (at start (connected ?from ?to)))
    :effect (and (at start (not (at ?from))) (at end (at ?to)))
  )
)
"""

_PROBLEM_PDDL = """(define (problem simple-problem)
  (:domain simple-temporal)
  (:objects a b - loc)
  (:init (at a) (connected a b))
  (:goal (at b))
  (:metric minimize (total-time))
)
"""

_TRAVEL_DOMAIN_PDDL = """(define (domain travel_domain)
 (:requirements :strips :typing :numeric-fluents)
 (:types location)
 (:predicates
   (is_at ?position - location)
   (is_connected ?l_from - location ?l_to - location)
 )
 (:functions
   (travel_time ?l_from - location ?l_to - location)
   (total_travel_time)
 )
 (:action move
  :parameters ( ?l_from - location ?l_to - location)
  :precondition (and
    (is_at ?l_from)
    (is_connected ?l_from ?l_to)
  )
  :effect (and
    (not (is_at ?l_from))
    (is_at ?l_to)
    (increase (total_travel_time) (travel_time ?l_from ?l_to))
  )
 )
)
"""

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

_CAVEDIVING_DOMAIN_PDDL = """(define (domain cave-diving-adl)
  (:requirements :typing :action-costs :adl :numeric-fluents)
  (:types location diver tank)
  (:predicates
    (holding ?d - diver ?t - tank)
    (full ?t - tank)
    (at-diver ?d - diver ?l - location)
    (at-surface ?d - diver)
    (decompressing ?d - diver)
    (cave-entrance ?l - location)
    (have-photo ?l - location)
  )
  (:functions
    (other-cost) - number
    (total-cost) - number
  )

  (:action enter-water
    :parameters (?d - diver ?l - location)
    :precondition (and (at-surface ?d) (cave-entrance ?l))
    :effect (and
      (not (at-surface ?d))
      (at-diver ?d ?l)
      (increase (total-cost) (other-cost))
    )
  )

  (:action photograph
    :parameters (?d - diver ?l - location ?t - tank)
    :precondition (and (at-diver ?d ?l) (holding ?d ?t) (full ?t))
    :effect (and
      (not (full ?t))
      (have-photo ?l)
      (increase (total-cost) (other-cost))
    )
  )

  (:action decompress
    :parameters (?d - diver ?l - location)
    :precondition (and (at-diver ?d ?l) (cave-entrance ?l))
    :effect (and
      (not (at-diver ?d ?l))
      (decompressing ?d)
      (increase (total-cost) (other-cost))
    )
  )
)
"""

_CAVEDIVING_PROBLEM_PDDL = """(define (problem cave-diving-adl-instance)
  (:domain cave-diving-adl)
  (:objects
    l0 - location
    d0 - diver
    t0 - tank
  )
  (:init
    (at-surface d0)
    (holding d0 t0)
    (full t0)
    (cave-entrance l0)
    (= (other-cost) 1)
    (= (total-cost) 0)
  )
  (:goal
    (and
      (have-photo l0)
      (decompressing d0)
    )
  )
  (:metric minimize (total-cost))
)
"""


def _write_input_dir(tmp_path: Path) -> Path:
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p01.pddl").write_text(_PROBLEM_PDDL, encoding="utf-8")
    return input_dir


def _run_or_skip(args: list[str]) -> int:
    """Invoke simulate_cli, skipping on the same UP-planner-unavailable conditions
    that test_simulator's existing planner test handles."""
    try:
        return simulate_main(args)
    except PermissionError as error:
        pytest.skip(f"UP planner unavailable: {error}")
    except Exception as error:
        if "Operation not permitted" in str(error):
            pytest.skip(f"UP planner unavailable: {error}")
        raise


def test_simulate_cli_emits_artifacts_for_a_solvable_problem(tmp_path: Path) -> None:
    input_dir = _write_input_dir(tmp_path)
    out_dir = tmp_path / "out"

    rc = _run_or_skip(["--input", str(input_dir), "--out", str(out_dir)])
    assert rc == 0

    # Session-level DB lives at the top of --out, not in the problem subdir.
    assert (out_dir / "simulation.duckdb").exists()

    problem_out = out_dir / "p01"
    assert (problem_out / "domain.pddl").exists()
    assert (problem_out / "p01.pddl").exists()
    assert not (problem_out / "simulation.duckdb").exists(), "DB must be session-level, not per-problem"
    assert (problem_out / "trace.json").exists()
    assert (problem_out / "plan.txt").exists()
    assert (problem_out / "manifest.json").exists()

    manifest = json.loads((problem_out / "manifest.json").read_text())
    assert manifest["goals_satisfied"] is True
    assert manifest["plan_topology"] in {"SequentialPlan", "TimeTriggeredPlan"}
    assert manifest["persist_backend"] == "duckdb"
    assert manifest["session_db"] == "../simulation.duckdb"

    aggregate = json.loads((out_dir / "manifest.json").read_text())
    assert len(aggregate["results"]) == 1
    assert aggregate["results"][0]["goals_satisfied"] is True
    assert aggregate["session_db"] == "simulation.duckdb"


def test_simulate_cli_missing_domain_returns_exit_2(tmp_path: Path) -> None:
    input_dir = tmp_path / "empty"
    input_dir.mkdir()
    (input_dir / "p01.pddl").write_text(_PROBLEM_PDDL, encoding="utf-8")
    out_dir = tmp_path / "out"

    rc = simulate_main(["--input", str(input_dir), "--out", str(out_dir)])
    assert rc == 2


def test_simulate_cli_missing_problem_returns_exit_2(tmp_path: Path) -> None:
    input_dir = tmp_path / "no-prob"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_DOMAIN_PDDL, encoding="utf-8")
    out_dir = tmp_path / "out"

    rc = simulate_main(["--input", str(input_dir), "--out", str(out_dir)])
    assert rc == 2


def test_simulate_cli_accepts_any_numeric_problem_suffix_and_sorts_numerically(tmp_path: Path) -> None:
    input_dir = tmp_path / "in-many"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p001.pddl").write_text(_PROBLEM_PDDL, encoding="utf-8")
    (input_dir / "p010.pddl").write_text(_PROBLEM_PDDL, encoding="utf-8")
    (input_dir / "p200.pddl").write_text(_PROBLEM_PDDL, encoding="utf-8")

    out_dir = tmp_path / "out-many"
    rc = _run_or_skip(["--input", str(input_dir), "--out", str(out_dir)])
    assert rc == 0

    aggregate = json.loads((out_dir / "manifest.json").read_text())
    assert [result["problem"] for result in aggregate["results"]] == ["p001", "p010", "p200"]
    assert (out_dir / "p001" / "manifest.json").exists()
    assert (out_dir / "p010" / "manifest.json").exists()
    assert (out_dir / "p200" / "manifest.json").exists()


def test_simulate_cli_persist_none_skips_db_file(tmp_path: Path) -> None:
    input_dir = _write_input_dir(tmp_path)
    out_dir = tmp_path / "out"
    rc = _run_or_skip(["--input", str(input_dir), "--out", str(out_dir), "--persist-backend", "none"])
    assert rc == 0

    # No DB at session level either when persist-backend is none.
    assert not (out_dir / "simulation.duckdb").exists()
    assert not (out_dir / "simulation.sqlite").exists()
    problem_out = out_dir / "p01"
    # Trace.json is independent of the DB; manifest still written.
    assert (problem_out / "trace.json").exists()


def test_simulate_cli_export_parquet_writes_parquet_files(tmp_path: Path) -> None:
    input_dir = _write_input_dir(tmp_path)
    out_dir = tmp_path / "out"
    rc = _run_or_skip(["--input", str(input_dir), "--out", str(out_dir), "--export-parquet"])
    assert rc == 0

    problem_out = out_dir / "p01"
    assert (problem_out / "snapshots.parquet").exists()
    assert (problem_out / "trace.parquet").exists()


def test_simulate_cli_session_db_holds_all_problems_with_distinct_run_ids(tmp_path: Path) -> None:
    """Multiple problems in --input share a single session DB; each gets its own run_id."""
    import duckdb

    input_dir = tmp_path / "in-multi"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_DOMAIN_PDDL, encoding="utf-8")
    # Two identical problems (same input file content) but different filenames.
    (input_dir / "p01.pddl").write_text(_PROBLEM_PDDL, encoding="utf-8")
    (input_dir / "p02.pddl").write_text(_PROBLEM_PDDL, encoding="utf-8")

    out_dir = tmp_path / "out-multi"
    rc = _run_or_skip(["--input", str(input_dir), "--out", str(out_dir)])
    assert rc == 0

    session_db = out_dir / "simulation.duckdb"
    assert session_db.exists()

    with duckdb.connect(str(session_db)) as con:
        run_ids = sorted(r[0] for r in con.execute("SELECT id FROM simulation_runs ORDER BY id").fetchall())
        snapshot_runs = sorted(set(r[0] for r in con.execute("SELECT DISTINCT run_id FROM state_snapshots").fetchall()))
    assert len(run_ids) == 2
    assert run_ids == snapshot_runs

    p01_manifest = json.loads((out_dir / "p01" / "manifest.json").read_text())
    p02_manifest = json.loads((out_dir / "p02" / "manifest.json").read_text())
    assert p01_manifest["run_id"] != p02_manifest["run_id"]
    assert {p01_manifest["run_id"], p02_manifest["run_id"]} == set(run_ids)


def test_simulate_cli_accepts_single_problem_pddl(tmp_path: Path) -> None:
    """Fallback path when input has `problem.pddl` instead of `pNN.pddl`."""
    input_dir = tmp_path / "single"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "problem.pddl").write_text(_PROBLEM_PDDL, encoding="utf-8")
    out_dir = tmp_path / "out"

    rc = _run_or_skip(["--input", str(input_dir), "--out", str(out_dir)])
    assert rc == 0
    assert (out_dir / "problem" / "manifest.json").exists()


def test_simulate_cli_handles_classical_travel_problem(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_dir = tmp_path / "travel"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_TRAVEL_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p001.pddl").write_text(_TRAVEL_PROBLEM_PDDL, encoding="utf-8")

    def _fake_solve(parsed_problem, planner_name, planner_timeout_seconds, **kwargs):
        move = parsed_problem.action("move")
        l1 = parsed_problem.object("l1")
        l2 = parsed_problem.object("l2")
        l3 = parsed_problem.object("l3")
        return _PlanningOutcome(
            plan=SequentialPlan(
                [
                    ActionInstance(move, (l1, l2)),
                    ActionInstance(move, (l2, l3)),
                ]
            ),
            planner_name="fake-classical-planner",
            planner_status=PlanGenerationResultStatus.SOLVED_SATISFICING.name,
            timeout_supported=True,
            requested_timeout_seconds=planner_timeout_seconds,
            timed_out=False,
            reason=None,
        )

    monkeypatch.setattr(simulate_cli, "_solve_plan", _fake_solve)

    out_dir = tmp_path / "travel-out"
    rc = simulate_main(["--input", str(input_dir), "--out", str(out_dir)])
    assert rc == 0

    manifest = json.loads((out_dir / "p001" / "manifest.json").read_text())
    assert manifest["goals_satisfied"] is True
    assert manifest["planner"] == "fake-classical-planner"
    assert manifest["plan_topology"] == "SequentialPlan"


def test_simulate_cli_defaults_planner_timeout_to_60_seconds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_dir = tmp_path / "timeout-default"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_TRAVEL_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p001.pddl").write_text(_TRAVEL_PROBLEM_PDDL, encoding="utf-8")

    seen: dict[str, float | None] = {"timeout": None}

    def _fake_solve(parsed_problem, planner_name, planner_timeout_seconds, **kwargs):
        seen["timeout"] = planner_timeout_seconds
        move = parsed_problem.action("move")
        l1 = parsed_problem.object("l1")
        l2 = parsed_problem.object("l2")
        l3 = parsed_problem.object("l3")
        return _PlanningOutcome(
            plan=SequentialPlan(
                [
                    ActionInstance(move, (l1, l2)),
                    ActionInstance(move, (l2, l3)),
                ]
            ),
            planner_name="fake-default-timeout-planner",
            planner_status=PlanGenerationResultStatus.SOLVED_SATISFICING.name,
            timeout_supported=True,
            requested_timeout_seconds=planner_timeout_seconds,
            timed_out=False,
            reason=None,
        )

    monkeypatch.setattr(simulate_cli, "_solve_plan", _fake_solve)

    out_dir = tmp_path / "timeout-default-out"
    rc = simulate_main(["--input", str(input_dir), "--out", str(out_dir)])
    assert rc == 0
    assert seen["timeout"] == 60.0

    manifest = json.loads((out_dir / "p001" / "manifest.json").read_text())
    assert manifest["planner_timeout_seconds"] == 60.0


def test_simulate_cli_handles_cavediving_problem_with_real_solver(tmp_path: Path) -> None:
    input_dir = tmp_path / "cavediving"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_CAVEDIVING_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p001.pddl").write_text(_CAVEDIVING_PROBLEM_PDDL, encoding="utf-8")

    out_dir = tmp_path / "cavediving-out"
    try:
        rc = simulate_main(["--input", str(input_dir), "--out", str(out_dir), "--planner", "fast-downward"])
    except Exception as error:
        if "fast-downward" in str(error).lower():
            pytest.skip(f"fast-downward unavailable in this environment: {error}")
        raise
    assert rc == 0

    manifest = json.loads((out_dir / "p001" / "manifest.json").read_text())
    assert manifest["goals_satisfied"] is True
    assert manifest["planner"].lower().replace(" ", "-") == "fast-downward"
    assert manifest["plan_topology"] == "SequentialPlan"


def test_simulate_cli_planner_timeout_is_logged_without_aborting_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import duckdb

    input_dir = tmp_path / "in-timeout"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_DOMAIN_PDDL, encoding="utf-8")
    ok_problem = _PROBLEM_PDDL.replace("simple-problem", "ok-problem")
    timeout_problem = _PROBLEM_PDDL.replace("simple-problem", "timeout-problem")
    (input_dir / "p001.pddl").write_text(timeout_problem, encoding="utf-8")
    (input_dir / "p002.pddl").write_text(ok_problem, encoding="utf-8")

    original_solve = simulate_cli._solve_plan

    def _fake_solve(parsed_problem, planner_name, planner_timeout_seconds, **kwargs):
        if parsed_problem.name == "timeout-problem":
            return _PlanningOutcome(
                plan=None,
                planner_name="fake-timeout-planner",
                planner_status=PlanGenerationResultStatus.TIMEOUT.name,
                timeout_supported=True,
                requested_timeout_seconds=planner_timeout_seconds,
                timed_out=True,
                reason="Planner timed out while solving timeout-problem.",
            )
        return original_solve(parsed_problem, planner_name, planner_timeout_seconds)

    monkeypatch.setattr(simulate_cli, "_solve_plan", _fake_solve)

    out_dir = tmp_path / "out-timeout"
    rc = _run_or_skip(["--input", str(input_dir), "--out", str(out_dir), "--planner-timeout", "1"])
    assert rc == 1

    aggregate = json.loads((out_dir / "manifest.json").read_text())
    assert [result["problem"] for result in aggregate["results"]] == ["p001", "p002"]

    timeout_result = aggregate["results"][0]
    assert timeout_result["status"] == "TIMEOUT"
    assert timeout_result["failure_stage"] == "plan"
    assert timeout_result["planner_status"] == "TIMEOUT"
    assert timeout_result["timed_out"] is True
    assert timeout_result["failure_reason"] == "Planner timed out while solving timeout-problem."

    success_result = aggregate["results"][1]
    assert success_result["status"] == "OK"
    assert success_result["planner_status"] in {"SOLVED_SATISFICING", "SOLVED_OPTIMALLY"}

    timeout_manifest = json.loads((out_dir / "p001" / "manifest.json").read_text())
    assert timeout_manifest["planner_status"] == "TIMEOUT"
    assert timeout_manifest["timed_out"] is True

    with duckdb.connect(str(out_dir / "simulation.duckdb")) as con:
        rows = con.execute(
            """
            SELECT problem_name, planner_name, requested_timeout_seconds, timeout_supported,
                   timed_out, status, failure_stage, reason
            FROM planner_attempts
            ORDER BY problem_name
            """
        ).fetchall()
    assert len(rows) == 2
    assert rows[0][0] == "p001"
    assert rows[0][2] == 1.0
    assert rows[0][3] is True
    assert rows[0][4] is True
    assert rows[0][5] == "TIMEOUT"
    assert rows[0][6] == "plan"
    assert rows[0][7] == "Planner timed out while solving timeout-problem."


def test_simulate_cli_jobs_uses_buffered_worker_persistence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import duckdb

    class InlineParallel:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def __call__(self, tasks):
            return [func(*args, **kwargs) for func, args, kwargs in tasks]

    input_dir = tmp_path / "parallel-travel"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_TRAVEL_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p001.pddl").write_text(_TRAVEL_PROBLEM_PDDL.replace("travel_demo", "travel_one"), encoding="utf-8")
    (input_dir / "p002.pddl").write_text(_TRAVEL_PROBLEM_PDDL.replace("travel_demo", "travel_two"), encoding="utf-8")

    def _fake_solve(parsed_problem, planner_name, planner_timeout_seconds, **kwargs):
        move = parsed_problem.action("move")
        l1 = parsed_problem.object("l1")
        l2 = parsed_problem.object("l2")
        l3 = parsed_problem.object("l3")
        return _PlanningOutcome(
            plan=SequentialPlan(
                [
                    ActionInstance(move, (l1, l2)),
                    ActionInstance(move, (l2, l3)),
                ]
            ),
            planner_name="fake-parallel-planner",
            planner_status=PlanGenerationResultStatus.SOLVED_SATISFICING.name,
            timeout_supported=True,
            requested_timeout_seconds=planner_timeout_seconds,
            timed_out=False,
            reason=None,
        )

    monkeypatch.setattr(simulate_cli, "Parallel", InlineParallel)
    monkeypatch.setattr(simulate_cli, "_solve_plan", _fake_solve)

    out_dir = tmp_path / "parallel-out"
    rc = simulate_main(["--input", str(input_dir), "--out", str(out_dir), "--jobs", "2"])
    assert rc == 0

    aggregate = json.loads((out_dir / "manifest.json").read_text())
    assert aggregate["jobs"] == 2
    assert [result["problem"] for result in aggregate["results"]] == ["p001", "p002"]
    assert [result["status"] for result in aggregate["results"]] == ["OK", "OK"]

    with duckdb.connect(str(out_dir / "simulation.duckdb")) as con:
        run_ids = [row[0] for row in con.execute("SELECT id FROM simulation_runs ORDER BY id").fetchall()]
        snapshot_runs = [
            row[0] for row in con.execute("SELECT DISTINCT run_id FROM state_snapshots ORDER BY run_id").fetchall()
        ]
        attempts = con.execute(
            "SELECT problem_name, planner_name, status FROM planner_attempts ORDER BY problem_name"
        ).fetchall()
    assert run_ids == [1, 2]
    assert snapshot_runs == run_ids
    assert attempts == [
        ("p001", "fake-parallel-planner", "SOLVED_SATISFICING"),
        ("p002", "fake-parallel-planner", "SOLVED_SATISFICING"),
    ]

    p001_manifest = json.loads((out_dir / "p001" / "manifest.json").read_text())
    p002_manifest = json.loads((out_dir / "p002" / "manifest.json").read_text())
    assert p001_manifest["run_id"] == 1
    assert p002_manifest["run_id"] == 2


def test_simulate_cli_rerun_timeouts_only_replaces_timeout_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_dir = tmp_path / "rerun-input"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_TRAVEL_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p001.pddl").write_text(_TRAVEL_PROBLEM_PDDL.replace("travel_demo", "travel_one"), encoding="utf-8")
    (input_dir / "p002.pddl").write_text(_TRAVEL_PROBLEM_PDDL.replace("travel_demo", "travel_two"), encoding="utf-8")

    out_dir = tmp_path / "rerun-out"
    out_dir.mkdir()
    previous = {
        "input": str(input_dir),
        "persist_backend": "duckdb",
        "session_db": "simulation.duckdb",
        "jobs": 1,
        "results": [
            {
                "problem": "p001",
                "goals_satisfied": False,
                "status": "TIMEOUT",
                "failure_stage": "plan",
                "failure_reason": "old timeout",
                "plan_topology": None,
                "planner": "old-planner",
                "planner_status": "TIMEOUT",
                "planner_timeout_seconds": 1.0,
                "planner_timeout_supported": True,
                "timed_out": True,
                "step_count": 0,
                "run_id": 10,
                "error": "old timeout",
            },
            {
                "problem": "p002",
                "goals_satisfied": True,
                "status": "OK",
                "failure_stage": None,
                "failure_reason": None,
                "plan_topology": "SequentialPlan",
                "planner": "old-planner",
                "planner_status": "SOLVED_SATISFICING",
                "planner_timeout_seconds": 1.0,
                "planner_timeout_supported": True,
                "timed_out": False,
                "step_count": 2,
                "run_id": 11,
                "error": None,
            },
        ],
    }
    (out_dir / "manifest.json").write_text(json.dumps(previous), encoding="utf-8")

    solved_names: list[str] = []

    def _fake_solve(parsed_problem, planner_name, planner_timeout_seconds, **kwargs):
        solved_names.append(parsed_problem.name)
        move = parsed_problem.action("move")
        l1 = parsed_problem.object("l1")
        l2 = parsed_problem.object("l2")
        l3 = parsed_problem.object("l3")
        return _PlanningOutcome(
            plan=SequentialPlan(
                [
                    ActionInstance(move, (l1, l2)),
                    ActionInstance(move, (l2, l3)),
                ]
            ),
            planner_name="rerun-planner",
            planner_status=PlanGenerationResultStatus.SOLVED_SATISFICING.name,
            timeout_supported=True,
            requested_timeout_seconds=planner_timeout_seconds,
            timed_out=False,
            reason=None,
        )

    monkeypatch.setattr(simulate_cli, "_solve_plan", _fake_solve)

    rc = simulate_main(["--input", str(input_dir), "--out", str(out_dir), "--rerun-timeouts"])
    assert rc == 0
    assert solved_names == ["travel_one"]

    aggregate = json.loads((out_dir / "manifest.json").read_text())
    assert aggregate["rerun"]["enabled"] is True
    assert aggregate["rerun"]["selected_count"] == 1
    assert aggregate["rerun"]["rerun_count"] == 1
    assert [result["problem"] for result in aggregate["results"]] == ["p001", "p002"]
    assert aggregate["results"][0]["status"] == "OK"
    assert aggregate["results"][0]["planner"] == "rerun-planner"
    assert aggregate["results"][1] == previous["results"][1]


def test_simulate_cli_rerun_timeouts_selects_timed_out_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_dir = tmp_path / "rerun-flag-input"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_TRAVEL_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p001.pddl").write_text(_TRAVEL_PROBLEM_PDDL, encoding="utf-8")

    out_dir = tmp_path / "rerun-flag-out"
    out_dir.mkdir()
    previous = {
        "results": [
            {
                "problem": "p001",
                "goals_satisfied": False,
                "status": "FAILED",
                "timed_out": True,
                "error": "planner timeout",
            }
        ]
    }
    (out_dir / "manifest.json").write_text(json.dumps(previous), encoding="utf-8")

    def _fake_solve(parsed_problem, planner_name, planner_timeout_seconds, **kwargs):
        move = parsed_problem.action("move")
        l1 = parsed_problem.object("l1")
        l2 = parsed_problem.object("l2")
        l3 = parsed_problem.object("l3")
        return _PlanningOutcome(
            plan=SequentialPlan([ActionInstance(move, (l1, l2)), ActionInstance(move, (l2, l3))]),
            planner_name="rerun-flag-planner",
            planner_status=PlanGenerationResultStatus.SOLVED_SATISFICING.name,
            timeout_supported=True,
            requested_timeout_seconds=planner_timeout_seconds,
            timed_out=False,
            reason=None,
        )

    monkeypatch.setattr(simulate_cli, "_solve_plan", _fake_solve)

    rc = simulate_main(["--input", str(input_dir), "--out", str(out_dir), "--rerun-timeouts"])
    assert rc == 0
    aggregate = json.loads((out_dir / "manifest.json").read_text())
    assert aggregate["results"][0]["status"] == "OK"
    assert aggregate["results"][0]["planner"] == "rerun-flag-planner"


def test_simulate_cli_rerun_timeouts_no_timeouts_exits_cleanly(tmp_path: Path) -> None:
    input_dir = tmp_path / "no-rerun-input"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_TRAVEL_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p001.pddl").write_text(_TRAVEL_PROBLEM_PDDL, encoding="utf-8")

    out_dir = tmp_path / "no-rerun-out"
    out_dir.mkdir()
    previous = {
        "input": str(input_dir),
        "persist_backend": "duckdb",
        "session_db": "simulation.duckdb",
        "jobs": 1,
        "results": [{"problem": "p001", "goals_satisfied": True, "status": "OK", "timed_out": False}],
    }
    (out_dir / "manifest.json").write_text(json.dumps(previous), encoding="utf-8")

    rc = simulate_main(["--input", str(input_dir), "--out", str(out_dir), "--rerun-timeouts"])
    assert rc == 0
    aggregate = json.loads((out_dir / "manifest.json").read_text())
    assert aggregate["rerun"]["selected_count"] == 0
    assert aggregate["rerun"]["rerun_count"] == 0
    assert aggregate["results"] == previous["results"]


def test_simulate_cli_rerun_timeouts_missing_manifest_returns_2(tmp_path: Path) -> None:
    input_dir = tmp_path / "missing-manifest-input"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_TRAVEL_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p001.pddl").write_text(_TRAVEL_PROBLEM_PDDL, encoding="utf-8")

    rc = simulate_main(["--input", str(input_dir), "--out", str(tmp_path / "missing-out"), "--rerun-timeouts"])
    assert rc == 2


def test_simulate_cli_rerun_timeouts_missing_input_problem_returns_2(tmp_path: Path) -> None:
    input_dir = tmp_path / "missing-problem-input"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_TRAVEL_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p001.pddl").write_text(_TRAVEL_PROBLEM_PDDL, encoding="utf-8")

    out_dir = tmp_path / "missing-problem-out"
    out_dir.mkdir()
    previous = {"results": [{"problem": "p999", "goals_satisfied": False, "status": "TIMEOUT", "timed_out": True}]}
    (out_dir / "manifest.json").write_text(json.dumps(previous), encoding="utf-8")

    rc = simulate_main(["--input", str(input_dir), "--out", str(out_dir), "--rerun-timeouts"])
    assert rc == 2


def test_simulate_cli_rerun_timeouts_works_with_jobs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class InlineParallel:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def __call__(self, tasks):
            return [func(*args, **kwargs) for func, args, kwargs in tasks]

    input_dir = tmp_path / "rerun-jobs-input"
    input_dir.mkdir()
    (input_dir / "domain.pddl").write_text(_TRAVEL_DOMAIN_PDDL, encoding="utf-8")
    (input_dir / "p001.pddl").write_text(_TRAVEL_PROBLEM_PDDL.replace("travel_demo", "travel_one"), encoding="utf-8")
    (input_dir / "p002.pddl").write_text(_TRAVEL_PROBLEM_PDDL.replace("travel_demo", "travel_two"), encoding="utf-8")

    out_dir = tmp_path / "rerun-jobs-out"
    out_dir.mkdir()
    previous = {
        "results": [
            {"problem": "p001", "goals_satisfied": False, "status": "TIMEOUT", "timed_out": True},
            {"problem": "p002", "goals_satisfied": True, "status": "OK", "timed_out": False},
        ]
    }
    (out_dir / "manifest.json").write_text(json.dumps(previous), encoding="utf-8")

    def _fake_solve(parsed_problem, planner_name, planner_timeout_seconds, **kwargs):
        move = parsed_problem.action("move")
        l1 = parsed_problem.object("l1")
        l2 = parsed_problem.object("l2")
        l3 = parsed_problem.object("l3")
        return _PlanningOutcome(
            plan=SequentialPlan([ActionInstance(move, (l1, l2)), ActionInstance(move, (l2, l3))]),
            planner_name="rerun-jobs-planner",
            planner_status=PlanGenerationResultStatus.SOLVED_SATISFICING.name,
            timeout_supported=True,
            requested_timeout_seconds=planner_timeout_seconds,
            timed_out=False,
            reason=None,
        )

    monkeypatch.setattr(simulate_cli, "Parallel", InlineParallel)
    monkeypatch.setattr(simulate_cli, "_solve_plan", _fake_solve)

    rc = simulate_main(["--input", str(input_dir), "--out", str(out_dir), "--rerun-timeouts", "--jobs", "2"])
    assert rc == 0
    aggregate = json.loads((out_dir / "manifest.json").read_text())
    assert aggregate["jobs"] == 2
    assert aggregate["rerun"]["rerun_count"] == 1
    assert aggregate["results"][0]["status"] == "OK"
    assert aggregate["results"][0]["planner"] == "rerun-jobs-planner"
    assert aggregate["results"][1] == previous["results"][1]
