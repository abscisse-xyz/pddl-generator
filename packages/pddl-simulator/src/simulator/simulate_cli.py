"""CLI for running PDDL simulations from a `pddl-cli dataset` output directory.

Workflow per invocation:

  --input DIR    must contain `domain.pddl` and one or more `p<digits>.pddl`
                 (or a single `problem.pddl`)
  --out DIR      destination; one subdirectory is written per problem
                 containing simulation.duckdb, trace.json, plan.txt,
                 manifest.json, plus the problem's domain/problem files
                 (echoed for self-contained replay)

Each problem is parsed, planned (auto via `OneshotPlanner` by default — see
``--planner``) with a default planner timeout of 60 seconds, replayed,
goal-checked, and persisted via
:class:`DuckDBStateStore`.
"""

from __future__ import annotations

import argparse
import inspect
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from joblib import Parallel, delayed

from .engine import SimulatorEngine
from .parser import PDDLSource, UnifiedPlanningParser
from .persistence import BufferedStateStore, DuckDBStateStore, SQLiteStateStore
from .persistence.buffered import action_record_to_grounded_action


@dataclass
class _ProblemTask:
    name: str
    domain_path: Path
    problem_path: Path


@dataclass
class _ProblemResult:
    name: str
    goals_satisfied: bool
    status: str
    failure_stage: str | None
    failure_reason: str | None
    plan_topology: str | None
    planner: str | None
    planner_status: str | None
    planner_timeout_seconds: float | None
    planner_timeout_supported: bool | None
    timed_out: bool
    step_count: int
    run_id: int | None = None
    error: str | None = None
    final_time: str | None = None


@dataclass
class _WorkerOptions:
    out_dir: Path
    planner_name: str | None
    planner_timeout_seconds: float | None
    persist_backend: str
    max_steps: int | None


@dataclass
class _WorkerResult:
    task: _ProblemTask
    result: _ProblemResult
    buffer: BufferedStateStore | None


@dataclass
class _PlanningOutcome:
    plan: Any | None
    planner_name: str | None
    planner_status: str
    timeout_supported: bool | None
    requested_timeout_seconds: float | None
    timed_out: bool
    reason: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pddl-simulator",
        description="Replay PDDL plans against the simulator and persist the trace.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Directory produced by `pddl-cli dataset` (must contain domain.pddl + p<digits>.pddl).",
    )
    parser.add_argument("--out", type=Path, default=Path("./out"), help="Output directory (default: ./out)")
    parser.add_argument(
        "--planner",
        type=str,
        default=None,
        help="Specific unified-planning planner name (default: auto-select via OneshotPlanner).",
    )
    parser.add_argument(
        "--planner-timeout",
        type=float,
        default=60.0,
        help=("Planner timeout in seconds when supported by the selected unified-planning engine (default: 60)."),
    )
    parser.add_argument(
        "--persist-backend",
        choices=("duckdb", "sqlite", "none"),
        default="duckdb",
        help="State-store backend (default: duckdb).",
    )
    parser.add_argument(
        "--export-parquet",
        action="store_true",
        help="After persistence, also emit per-problem snapshots.parquet and trace.parquet (DuckDB only).",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Hard cap on simulation steps per problem (default: unlimited).",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Number of problems to solve/simulate in parallel with joblib (default: 1).",
    )
    parser.add_argument(
        "--rerun-timeouts",
        action="store_true",
        help="Rerun only problems marked TIMEOUT/timed_out in a previous simulation manifest.",
    )
    parser.add_argument(
        "--rerun-from",
        type=Path,
        default=None,
        help="Previous simulation output directory or manifest.json for --rerun-timeouts (default: --out).",
    )
    return parser


def _discover_problems(input_dir: Path) -> tuple[Path, list[_ProblemTask]]:
    domain_path = input_dir / "domain.pddl"
    if not domain_path.is_file():
        raise FileNotFoundError(f"--input {input_dir} is missing domain.pddl")

    numbered_problem_pattern = re.compile(r"^p(\d+)\.pddl$")
    numbered_problems: list[tuple[int, str, Path]] = []
    for candidate in input_dir.iterdir():
        if not candidate.is_file():
            continue
        match = numbered_problem_pattern.fullmatch(candidate.name)
        if match is None:
            continue
        numbered_problems.append((int(match.group(1)), candidate.name, candidate))

    numbered_problems.sort(key=lambda item: (item[0], item[1]))
    if numbered_problems:
        tasks = [
            _ProblemTask(name=problem_path.stem, domain_path=domain_path, problem_path=problem_path)
            for _, _, problem_path in numbered_problems
        ]
    elif (input_dir / "problem.pddl").is_file():
        tasks = [_ProblemTask(name="problem", domain_path=domain_path, problem_path=input_dir / "problem.pddl")]
    else:
        raise FileNotFoundError(f"--input {input_dir} has no p<digits>.pddl or problem.pddl")
    return domain_path, tasks


def _solve_plan(
    parsed_problem: Any,
    planner_name: str | None,
    planner_timeout_seconds: float | None,
    *,
    domain_path: Path | None = None,
    problem_path: Path | None = None,
) -> _PlanningOutcome:
    """Compute a plan and return structured planner metadata."""
    from unified_planning.engines.results import PlanGenerationResultStatus
    from unified_planning.shortcuts import OneshotPlanner, get_environment

    get_environment().credits_stream = None

    if planner_name is not None:
        ctx = OneshotPlanner(name=planner_name)
    else:
        ctx = OneshotPlanner(problem_kind=parsed_problem.kind)
    with ctx as planner:
        timeout_supported = "timeout" in inspect.signature(planner.solve).parameters
        solve_kwargs: dict[str, Any] = {}
        if planner_timeout_seconds is not None and timeout_supported:
            solve_kwargs["timeout"] = planner_timeout_seconds
        result = planner.solve(parsed_problem, **solve_kwargs)

    planner_name_used = planner.name
    status_name = result.status.name
    timed_out = result.status == PlanGenerationResultStatus.TIMEOUT
    log_messages = result.log_messages or []
    log_suffix = "; ".join(f"{entry.level.name}: {entry.message}" for entry in log_messages if entry.message)

    reason: str | None = None
    if planner_timeout_seconds is not None and not timeout_supported:
        reason = (
            f"Planner {planner_name_used} does not expose a timeout parameter; "
            f"requested timeout={planner_timeout_seconds}s was not enforced."
        )
    if result.plan is None:
        base_reason = f"Planner returned no plan (status={status_name})."
        if log_suffix:
            base_reason = f"{base_reason} Logs: {log_suffix}"
        if reason is None:
            reason = base_reason
        else:
            reason = f"{reason} {base_reason}"
    elif log_suffix and reason is None:
        reason = f"Planner logs: {log_suffix}"

    return _PlanningOutcome(
        plan=result.plan,
        planner_name=planner_name_used,
        planner_status=status_name,
        timeout_supported=timeout_supported,
        requested_timeout_seconds=planner_timeout_seconds,
        timed_out=timed_out,
        reason=reason,
    )


def _format_plan_text(plan: Any) -> str:
    """Best-effort human-readable plan dump for plan.txt."""
    type_name = type(plan).__name__
    if type_name == "SequentialPlan":
        return "\n".join(str(action) for action in plan.actions) + "\n"
    if type_name == "TimeTriggeredPlan":
        lines = []
        for start, action, duration in plan.timed_actions:
            duration_part = f" [{duration}]" if duration is not None else ""
            lines.append(f"{start}: {action}{duration_part}")
        return "\n".join(lines) + "\n"
    if type_name == "HierarchicalPlan":
        inner = getattr(plan, "action_plan", None)
        if inner is not None:
            return "# HierarchicalPlan, flat plan below\n" + _format_plan_text(inner)
    return f"# unhandled plan type: {type_name}\n{plan!r}\n"


def _serialize_trace(engine: SimulatorEngine) -> list[dict[str, Any]]:
    return [
        {
            "time": f"{entry.time.numerator}/{entry.time.denominator}",
            "kind": entry.kind.value,
            "description": entry.description,
        }
        for entry in engine.trace.entries
    ]


def _make_state_store(backend: str, db_path: Path):
    if backend == "duckdb":
        return DuckDBStateStore(db_path)
    if backend == "sqlite":
        return SQLiteStateStore(db_path)
    return None  # backend == "none"


def _manifest_path_from_rerun_source(source: Path) -> Path:
    return source if source.name == "manifest.json" else source / "manifest.json"


def _load_previous_manifest(source: Path) -> dict[str, Any]:
    manifest_path = _manifest_path_from_rerun_source(source)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"--rerun-timeouts could not find previous manifest: {manifest_path}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{manifest_path} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{manifest_path} must contain a JSON object")
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError(f"{manifest_path} must contain a list field named 'results'")
    return payload


def _timeout_problem_names(manifest: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for item in manifest.get("results", []):
        if not isinstance(item, dict):
            continue
        problem = item.get("problem")
        if not isinstance(problem, str):
            continue
        if item.get("status") == "TIMEOUT" or item.get("timed_out") is True:
            names.add(problem)
    return names


def _filter_rerun_tasks(tasks: list[_ProblemTask], timeout_names: set[str]) -> list[_ProblemTask]:
    task_names = {task.name for task in tasks}
    missing = sorted(timeout_names - task_names)
    if missing:
        raise FileNotFoundError("previous timeout problem(s) are missing from --input: " + ", ".join(missing))
    return [task for task in tasks if task.name in timeout_names]


def _result_to_manifest_entry(result: _ProblemResult) -> dict[str, Any]:
    return {
        "problem": result.name,
        "goals_satisfied": result.goals_satisfied,
        "status": result.status,
        "failure_stage": result.failure_stage,
        "failure_reason": result.failure_reason,
        "plan_topology": result.plan_topology,
        "planner": result.planner,
        "planner_status": result.planner_status,
        "planner_timeout_seconds": result.planner_timeout_seconds,
        "planner_timeout_supported": result.planner_timeout_supported,
        "timed_out": result.timed_out,
        "step_count": result.step_count,
        "run_id": result.run_id,
        "error": result.error,
    }


def _build_aggregate_manifest(
    *,
    input_dir: Path,
    persist_backend: str,
    db_filename: str | None,
    jobs: int,
    results: list[_ProblemResult],
) -> dict[str, Any]:
    return {
        "input": str(input_dir.resolve()),
        "persist_backend": persist_backend,
        "session_db": db_filename,
        "jobs": jobs,
        "results": [_result_to_manifest_entry(result) for result in results],
    }


def _merge_rerun_manifest(
    previous_manifest: dict[str, Any],
    new_manifest: dict[str, Any],
    *,
    rerun_source: Path,
    selected_problem_names: set[str],
) -> dict[str, Any]:
    replacements = {
        result["problem"]: result
        for result in new_manifest["results"]
        if isinstance(result, dict) and isinstance(result.get("problem"), str)
    }

    previous_results = previous_manifest.get("results", [])
    merged_results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in previous_results:
        if not isinstance(item, dict):
            continue
        problem = item.get("problem")
        if isinstance(problem, str) and problem in replacements:
            merged_results.append(replacements[problem])
            seen.add(problem)
        else:
            merged_results.append(item)
            if isinstance(problem, str):
                seen.add(problem)

    for problem, result in replacements.items():
        if problem not in seen:
            merged_results.append(result)

    merged = dict(previous_manifest)
    merged.update(
        {
            "input": new_manifest["input"],
            "persist_backend": new_manifest["persist_backend"],
            "session_db": new_manifest["session_db"],
            "jobs": new_manifest["jobs"],
            "results": merged_results,
            "rerun": {
                "enabled": True,
                "source": str(_manifest_path_from_rerun_source(rerun_source).resolve()),
                "selected_statuses": ["TIMEOUT"],
                "selected_count": len(selected_problem_names),
                "rerun_count": len(replacements),
            },
        }
    )
    return merged


def _append_planner_attempt(
    store,
    *,
    run_id: int | None,
    problem_name: str,
    planner_name: str | None,
    planner_timeout_seconds: float | None,
    planner_timeout_supported: bool | None,
    timed_out: bool,
    planner_status: str | None,
    failure_stage: str,
    failure_reason: str | None,
    plan_topology: str | None = None,
) -> None:
    if store is None or run_id is None:
        return
    store.append_planner_attempt(
        run_id=run_id,
        problem_name=problem_name,
        planner_name=planner_name,
        requested_timeout_seconds=planner_timeout_seconds,
        timeout_supported=planner_timeout_supported,
        timed_out=timed_out,
        status=planner_status or "UNKNOWN",
        failure_stage=failure_stage,
        reason=failure_reason,
        plan_topology=plan_topology,
    )


def _write_problem_manifest(
    *,
    problem_out: Path,
    task: _ProblemTask,
    persist_backend: str,
    result: _ProblemResult,
    final_time: str | None = None,
) -> None:
    manifest = {
        "problem": task.name,
        "domain_file": "domain.pddl",
        "problem_file": task.problem_path.name,
        "planner": result.planner,
        "planner_status": result.planner_status,
        "planner_timeout_seconds": result.planner_timeout_seconds,
        "planner_timeout_supported": result.planner_timeout_supported,
        "timed_out": result.timed_out,
        "status": result.status,
        "failure_stage": result.failure_stage,
        "failure_reason": result.failure_reason,
        "plan_topology": result.plan_topology,
        "persist_backend": persist_backend,
        "goals_satisfied": result.goals_satisfied,
        "step_count": result.step_count,
        "run_id": result.run_id,
        "session_db": "../simulation.duckdb"
        if persist_backend == "duckdb"
        else ("../simulation.sqlite" if persist_backend == "sqlite" else None),
        "final_time": final_time if final_time is not None else result.final_time,
    }
    (problem_out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _simulate_one(
    task: _ProblemTask,
    out_dir: Path,
    store,
    planner_name: str | None,
    planner_timeout_seconds: float | None,
    persist_backend: str,
    max_steps: int | None,
    export_parquet: bool,
) -> _ProblemResult:
    problem_out = out_dir / task.name
    problem_out.mkdir(parents=True, exist_ok=True)

    # Echo input files for self-contained replay.
    shutil.copy2(task.domain_path, problem_out / "domain.pddl")
    shutil.copy2(task.problem_path, problem_out / task.problem_path.name)

    run_id: int | None = None
    if store is not None:
        run = store.create_run(domain_name=None, problem_name=task.name)
        run_id = run.run_id

    parser = UnifiedPlanningParser()
    try:
        runtime = parser.load_runtime(PDDLSource(domain_path=task.domain_path, problem_path=task.problem_path))
    except Exception as exc:  # noqa: BLE001
        result = _ProblemResult(
            name=task.name,
            goals_satisfied=False,
            status="FAILED",
            failure_stage="parse",
            failure_reason=f"{type(exc).__name__}: {exc}",
            plan_topology=None,
            planner=None,
            planner_status=None,
            planner_timeout_seconds=planner_timeout_seconds,
            planner_timeout_supported=None,
            timed_out=False,
            step_count=0,
            run_id=run_id,
            error=f"{type(exc).__name__}: {exc}",
        )
        _append_planner_attempt(
            store,
            run_id=run_id,
            problem_name=task.name,
            planner_name=planner_name,
            planner_timeout_seconds=planner_timeout_seconds,
            planner_timeout_supported=None,
            timed_out=False,
            planner_status="PARSE_ERROR",
            failure_stage="parse",
            failure_reason=result.failure_reason,
        )
        _write_problem_manifest(problem_out=problem_out, task=task, persist_backend=persist_backend, result=result)
        return result

    try:
        planning = _solve_plan(
            runtime.source_problem,
            planner_name,
            planner_timeout_seconds,
            domain_path=task.domain_path,
            problem_path=task.problem_path,
        )
    except Exception as exc:  # noqa: BLE001
        result = _ProblemResult(
            name=task.name,
            goals_satisfied=False,
            status="FAILED",
            failure_stage="plan",
            failure_reason=f"{type(exc).__name__}: {exc}",
            plan_topology=None,
            planner=planner_name,
            planner_status="EXCEPTION",
            planner_timeout_seconds=planner_timeout_seconds,
            planner_timeout_supported=None,
            timed_out=False,
            step_count=0,
            run_id=run_id,
            error=f"{type(exc).__name__}: {exc}",
        )
        _append_planner_attempt(
            store,
            run_id=run_id,
            problem_name=task.name,
            planner_name=planner_name,
            planner_timeout_seconds=planner_timeout_seconds,
            planner_timeout_supported=None,
            timed_out=False,
            planner_status="EXCEPTION",
            failure_stage="plan",
            failure_reason=result.failure_reason,
        )
        _write_problem_manifest(problem_out=problem_out, task=task, persist_backend=persist_backend, result=result)
        return result

    plan = planning.plan
    planner_used = planning.planner_name
    plan_topology = type(plan).__name__ if plan is not None else None
    if plan is None:
        status = "TIMEOUT" if planning.timed_out else "FAILED"
        result = _ProblemResult(
            name=task.name,
            goals_satisfied=False,
            status=status,
            failure_stage="plan",
            failure_reason=planning.reason,
            plan_topology=plan_topology,
            planner=planner_used,
            planner_status=planning.planner_status,
            planner_timeout_seconds=planning.requested_timeout_seconds,
            planner_timeout_supported=planning.timeout_supported,
            timed_out=planning.timed_out,
            step_count=0,
            run_id=run_id,
            error=planning.reason,
        )
        _append_planner_attempt(
            store,
            run_id=run_id,
            problem_name=task.name,
            planner_name=planner_used,
            planner_timeout_seconds=planning.requested_timeout_seconds,
            planner_timeout_supported=planning.timeout_supported,
            timed_out=planning.timed_out,
            planner_status=planning.planner_status,
            failure_stage="plan",
            failure_reason=planning.reason,
            plan_topology=plan_topology,
        )
        (problem_out / "plan.txt").write_text(_format_plan_text(plan), encoding="utf-8")
        _write_problem_manifest(problem_out=problem_out, task=task, persist_backend=persist_backend, result=result)
        return result

    engine = SimulatorEngine.from_runtime(runtime)
    if store is not None:
        engine.state_store = store
        if run_id is not None:
            engine.prepare_persisted_run(run_id)

    try:
        engine.replay_plan(plan)
        engine.run_to_completion(max_steps=max_steps)
        ok = engine.goals_satisfied()
    except Exception as exc:  # noqa: BLE001 — surface any failure into the manifest
        (problem_out / "plan.txt").write_text(_format_plan_text(plan), encoding="utf-8")
        result = _ProblemResult(
            name=task.name,
            goals_satisfied=False,
            status="FAILED",
            failure_stage="simulate",
            failure_reason=f"{type(exc).__name__}: {exc}",
            plan_topology=plan_topology,
            planner=planner_used,
            planner_status=planning.planner_status,
            planner_timeout_seconds=planning.requested_timeout_seconds,
            planner_timeout_supported=planning.timeout_supported,
            timed_out=planning.timed_out,
            step_count=engine.step_index,
            run_id=engine.run_id,
            error=f"{type(exc).__name__}: {exc}",
        )
        _append_planner_attempt(
            store,
            run_id=engine.run_id,
            problem_name=task.name,
            planner_name=planner_used,
            planner_timeout_seconds=planning.requested_timeout_seconds,
            planner_timeout_supported=planning.timeout_supported,
            timed_out=planning.timed_out,
            planner_status=planning.planner_status,
            failure_stage="simulate",
            failure_reason=result.failure_reason,
            plan_topology=plan_topology,
        )
        _write_problem_manifest(problem_out=problem_out, task=task, persist_backend=persist_backend, result=result)
        return result

    (problem_out / "plan.txt").write_text(_format_plan_text(plan), encoding="utf-8")
    (problem_out / "trace.json").write_text(json.dumps(_serialize_trace(engine), indent=2), encoding="utf-8")

    if export_parquet:
        try:
            if not isinstance(store, DuckDBStateStore):
                raise ValueError("--export-parquet requires --persist-backend duckdb")
            if engine.run_id is not None:
                store.export_parquet(engine.run_id, problem_out)
        except Exception as exc:  # noqa: BLE001
            result = _ProblemResult(
                name=task.name,
                goals_satisfied=False,
                status="FAILED",
                failure_stage="export",
                failure_reason=f"{type(exc).__name__}: {exc}",
                plan_topology=plan_topology,
                planner=planner_used,
                planner_status=planning.planner_status,
                planner_timeout_seconds=planning.requested_timeout_seconds,
                planner_timeout_supported=planning.timeout_supported,
                timed_out=planning.timed_out,
                step_count=engine.step_index,
                run_id=engine.run_id,
                error=f"{type(exc).__name__}: {exc}",
            )
            _append_planner_attempt(
                store,
                run_id=engine.run_id,
                problem_name=task.name,
                planner_name=planner_used,
                planner_timeout_seconds=planning.requested_timeout_seconds,
                planner_timeout_supported=planning.timeout_supported,
                timed_out=planning.timed_out,
                planner_status=planning.planner_status,
                failure_stage="export",
                failure_reason=result.failure_reason,
                plan_topology=plan_topology,
            )
            _write_problem_manifest(problem_out=problem_out, task=task, persist_backend=persist_backend, result=result)
            return result

    result = _ProblemResult(
        name=task.name,
        goals_satisfied=ok,
        status="OK" if ok else "GOALS_NOT_SATISFIED",
        failure_stage=None if ok else "goals",
        failure_reason=None if ok else "Simulation completed but goals are not satisfied.",
        plan_topology=plan_topology,
        planner=planner_used,
        planner_status=planning.planner_status,
        planner_timeout_seconds=planning.requested_timeout_seconds,
        planner_timeout_supported=planning.timeout_supported,
        timed_out=planning.timed_out,
        step_count=engine.step_index,
        run_id=engine.run_id,
        final_time=f"{engine.state.time.numerator}/{engine.state.time.denominator}",
    )
    _append_planner_attempt(
        store,
        run_id=engine.run_id,
        problem_name=task.name,
        planner_name=planner_used,
        planner_timeout_seconds=planning.requested_timeout_seconds,
        planner_timeout_supported=planning.timeout_supported,
        timed_out=planning.timed_out,
        planner_status=planning.planner_status,
        failure_stage="completed" if ok else "goals",
        failure_reason=result.failure_reason or planning.reason,
        plan_topology=plan_topology,
    )
    _write_problem_manifest(
        problem_out=problem_out,
        task=task,
        persist_backend=persist_backend,
        result=result,
    )
    return result


def _simulate_one_worker(task: _ProblemTask, options: _WorkerOptions) -> _WorkerResult:
    store = BufferedStateStore() if options.persist_backend != "none" else None
    try:
        result = _simulate_one(
            task=task,
            out_dir=options.out_dir,
            store=store,
            planner_name=options.planner_name,
            planner_timeout_seconds=options.planner_timeout_seconds,
            persist_backend=options.persist_backend,
            max_steps=options.max_steps,
            export_parquet=False,
        )
    except Exception as exc:  # noqa: BLE001
        problem_out = options.out_dir / task.name
        problem_out.mkdir(parents=True, exist_ok=True)
        result = _ProblemResult(
            name=task.name,
            goals_satisfied=False,
            status="FAILED",
            failure_stage="worker",
            failure_reason=f"{type(exc).__name__}: {exc}",
            plan_topology=None,
            planner=options.planner_name,
            planner_status="EXCEPTION",
            planner_timeout_seconds=options.planner_timeout_seconds,
            planner_timeout_supported=None,
            timed_out=False,
            step_count=0,
            run_id=None,
            error=f"{type(exc).__name__}: {exc}",
        )
        _write_problem_manifest(
            problem_out=problem_out,
            task=task,
            persist_backend=options.persist_backend,
            result=result,
        )
    return _WorkerResult(task=task, result=result, buffer=store)


def _flush_buffered_store(buffer: BufferedStateStore, store) -> dict[int, int]:
    run_id_map: dict[int, int] = {}
    for run in buffer.runs:
        persisted = store.create_run(domain_name=run.domain_name, problem_name=run.problem_name)
        run_id_map[run.run_id] = persisted.run_id

    for model in buffer.problem_models:
        store.persist_problem_model(
            run_id=run_id_map[model.run_id],
            domain=model.domain,
            problem=model.problem,
        )

    for snapshot in buffer.snapshots:
        store.save_snapshot(
            run_id=run_id_map[snapshot.run_id],
            step_index=snapshot.step_index,
            sim_time=snapshot.sim_time,
            reason=snapshot.reason,
            state=snapshot.state,
            pending_events=snapshot.pending_events,
        )

    for local_run_id, step_index, entry in buffer.trace_entries:
        store.append_trace_entry(run_id=run_id_map[local_run_id], step_index=step_index, entry=entry)

    for event in buffer.action_events:
        store.append_action_event(
            run_id=run_id_map[event.run_id],
            step_index=event.step_index,
            sim_time=event.sim_time,
            phase=event.phase,
            action=action_record_to_grounded_action(event),
        )

    for attempt in buffer.planner_attempts:
        store.append_planner_attempt(
            run_id=run_id_map[attempt.run_id],
            problem_name=attempt.problem_name,
            planner_name=attempt.planner_name,
            requested_timeout_seconds=attempt.requested_timeout_seconds,
            timeout_supported=attempt.timeout_supported,
            timed_out=attempt.timed_out,
            status=attempt.status,
            failure_stage=attempt.failure_stage,
            reason=attempt.reason,
            plan_topology=attempt.plan_topology,
        )

    return run_id_map


def _should_attempt_export(result: _ProblemResult) -> bool:
    return result.failure_stage in {None, "goals"}


def _mark_export_failure(result: _ProblemResult, exc: Exception) -> None:
    result.goals_satisfied = False
    result.status = "FAILED"
    result.failure_stage = "export"
    result.failure_reason = f"{type(exc).__name__}: {exc}"
    result.error = result.failure_reason


def _finalize_worker_result(
    worker_result: _WorkerResult,
    *,
    out_dir: Path,
    store,
    persist_backend: str,
    export_parquet: bool,
) -> _ProblemResult:
    result = worker_result.result
    if store is not None and worker_result.buffer is not None:
        run_id_map = _flush_buffered_store(worker_result.buffer, store)
        if result.run_id is not None:
            result.run_id = run_id_map.get(result.run_id, result.run_id)
        elif len(run_id_map) == 1:
            result.run_id = next(iter(run_id_map.values()))

    if export_parquet and _should_attempt_export(result):
        try:
            if not isinstance(store, DuckDBStateStore):
                raise ValueError("--export-parquet requires --persist-backend duckdb")
            if result.run_id is None:
                raise ValueError("cannot export parquet without a persisted run_id")
            store.export_parquet(result.run_id, out_dir / worker_result.task.name)
        except Exception as exc:  # noqa: BLE001
            _mark_export_failure(result, exc)
            _append_planner_attempt(
                store,
                run_id=result.run_id,
                problem_name=worker_result.task.name,
                planner_name=result.planner,
                planner_timeout_seconds=result.planner_timeout_seconds,
                planner_timeout_supported=result.planner_timeout_supported,
                timed_out=result.timed_out,
                planner_status=result.planner_status,
                failure_stage="export",
                failure_reason=result.failure_reason,
                plan_topology=result.plan_topology,
            )

    _write_problem_manifest(
        problem_out=out_dir / worker_result.task.name,
        task=worker_result.task,
        persist_backend=persist_backend,
        result=result,
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_dir: Path = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.jobs < 1:
        print("--jobs must be >= 1", file=sys.stderr)
        return 2

    input_dir = args.input.resolve()
    try:
        _, tasks = _discover_problems(input_dir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    previous_manifest: dict[str, Any] | None = None
    rerun_source: Path | None = None
    selected_timeout_names: set[str] = set()
    if args.rerun_timeouts:
        rerun_source = (args.rerun_from or out_dir).resolve()
        try:
            previous_manifest = _load_previous_manifest(rerun_source)
            selected_timeout_names = _timeout_problem_names(previous_manifest)
            tasks = _filter_rerun_tasks(tasks, selected_timeout_names)
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2

        if not tasks:
            db_filename = previous_manifest.get("session_db")
            aggregate = _merge_rerun_manifest(
                previous_manifest,
                {
                    "input": str(input_dir),
                    "persist_backend": previous_manifest.get("persist_backend", args.persist_backend),
                    "session_db": db_filename if isinstance(db_filename, str) else None,
                    "jobs": args.jobs,
                    "results": [],
                },
                rerun_source=rerun_source,
                selected_problem_names=selected_timeout_names,
            )
            (out_dir / "manifest.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
            print("no timed-out problem(s) to rerun")
            return 0

    # One state-store per session. Each problem becomes a separate `simulation_runs`
    # row; downstream queries join state_snapshots / trace_entries by `run_id`.
    db_filename = {"duckdb": "simulation.duckdb", "sqlite": "simulation.sqlite"}.get(args.persist_backend)
    session_store = _make_state_store(args.persist_backend, out_dir / db_filename) if db_filename else None

    results: list[_ProblemResult] = []
    if args.jobs == 1:
        for task in tasks:
            results.append(
                _simulate_one(
                    task=task,
                    out_dir=out_dir,
                    store=session_store,
                    planner_name=args.planner,
                    planner_timeout_seconds=args.planner_timeout,
                    persist_backend=args.persist_backend,
                    max_steps=args.max_steps,
                    export_parquet=args.export_parquet,
                )
            )
    else:
        worker_options = _WorkerOptions(
            out_dir=out_dir,
            planner_name=args.planner,
            planner_timeout_seconds=args.planner_timeout,
            persist_backend=args.persist_backend,
            max_steps=args.max_steps,
        )
        worker_results = Parallel(n_jobs=args.jobs, backend="loky")(
            delayed(_simulate_one_worker)(task, worker_options) for task in tasks
        )
        results = [
            _finalize_worker_result(
                worker_result,
                out_dir=out_dir,
                store=session_store,
                persist_backend=args.persist_backend,
                export_parquet=args.export_parquet,
            )
            for worker_result in worker_results
        ]

    aggregate = _build_aggregate_manifest(
        input_dir=input_dir,
        persist_backend=args.persist_backend,
        db_filename=db_filename,
        jobs=args.jobs,
        results=results,
    )
    if previous_manifest is not None and rerun_source is not None:
        aggregate = _merge_rerun_manifest(
            previous_manifest,
            aggregate,
            rerun_source=rerun_source,
            selected_problem_names=selected_timeout_names,
        )
    (out_dir / "manifest.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")

    result_entries = (
        aggregate["results"]
        if previous_manifest is not None
        else [_result_to_manifest_entry(result) for result in results]
    )
    failures = [
        item
        for item in result_entries
        if isinstance(item, dict) and (item.get("error") is not None or item.get("goals_satisfied") is not True)
    ]
    if failures:
        print(
            f"{len(failures)} of {len(result_entries)} problem(s) failed to satisfy goals; see manifest.",
            file=sys.stderr,
        )
        return 1

    if previous_manifest is not None:
        print(f"reran {len(results)} timed-out problem(s) into {out_dir}")
    else:
        print(f"simulated {len(results)} problem(s) into {out_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
