# pddl-simulator

Library for replaying PDDL plans against an event-driven kernel and
persisting state snapshots + traces to a queryable store. Used by the
[`pddl-cli simulate`](../../README.md#simulation) subcommand.

## Where this fits

This package is **not the user-facing CLI**. End users go through
[`pddl-cli`](../../pddl-cli/) at the repo root, which exposes the simulator
as `pddl-cli simulate …`. Build and invoke the project from the
[top-level README](../../README.md).

This README focuses on the *library* — the pieces under
[src/simulator/](src/simulator/).

## Components

| Module | Purpose |
|---|---|
| [model.py](src/simulator/model.py) | `SimulationDomain`, `SimulationProblem`, `DurativeActionSchema`, `GroundedAction` data classes |
| [state.py](src/simulator/state.py) | Mutable `SimulationState` (facts, numeric fluents, running actions) |
| [events.py](src/simulator/events.py) | `EventKind`, `ScheduledEvent` for the priority-queue kernel |
| [trace.py](src/simulator/trace.py) | `SimulationTrace` (in-memory ordered event log) |
| [parser.py](src/simulator/parser.py) | `UnifiedPlanningParser`: load PDDL via `unified_planning.io.PDDLReader`, normalize action schemas, build initial state |
| [engine.py](src/simulator/engine.py) | `SimulatorEngine`: the event-driven runtime. Supports `step`, `run_until`, `run_to_completion`, `replay_plan`, `goals_satisfied`, with optional pluggable persistence |
| [persistence/](src/simulator/persistence/) | `StateStore` Protocol with `DuckDBStateStore` (default) and `SQLiteStateStore` impls |
| [simulate_cli.py](src/simulator/simulate_cli.py) | argparse-based CLI; the entry point `pddl-cli simulate` delegates to its `main()` |

## Plan-topology coverage

`SimulatorEngine.replay_plan` accepts:

- **`SequentialPlan`** — total order; runs each action for its declared duration.
- **`TimeTriggeredPlan`** — start times + (optional) durations; events scheduled and drained in time order.
- **`HierarchicalPlan`** — unwrapped to its `action_plan` (decomposition is not currently captured in the trace).

Unsupported (raises `NotImplementedError` with guidance):
`PartialOrderPlan`, `STNPlan`, `ContingentPlan`, scheduling-specific plan
objects. Linearize / schedule them first if you need to replay.

The engine grounds actions lazily when a plan action is replayed. It does not
materialize the full action universe for normal simulation, which keeps large
classical domains from spending time on actions that never occur in the
trajectory.

## Persistence

The engine accepts any `state_store: StateStore` (Protocol), so analytical
backends are interchangeable.

### DuckDB store (default)

[`DuckDBStateStore`](src/simulator/persistence/duckdb_store.py) stores
snapshots with native `LIST<STRUCT(...)>` columns — no JSON parsing for
analytical queries. Adds `iter_snapshots(run_id, *, since, until, stride)`
for trajectory streaming and `export_parquet(run_id, out_dir)` for ML-pipeline
export. It also creates a `state_action_transitions` view that joins executed
actions with their before/after snapshots for `(state, action, next_state)`
training data.

```python
from simulator import DuckDBStateStore, SimulatorEngine
store = DuckDBStateStore("./run.duckdb")
engine = SimulatorEngine.from_pddl(domain_path, problem_path)
engine.state_store = store
engine.reset()
engine.replay_plan(plan)
```

### SQLite store

[`SQLiteStateStore`](src/simulator/persistence/sqlite.py) preserves the
original JSON-text layout for callers that don't want a DuckDB dependency.
Same Protocol; same call sites.

## Running tests

```sh
uv run pytest packages/pddl-simulator/tests
```

Tests use the migrated sailing generators from `pddl-dataset` (declared as a
test-only `dev` dependency); a small shim in
[tests/_sailing_helpers.py](tests/_sailing_helpers.py) preserves the legacy
`generate_problem_pddl(name, num_boats, …)` signature.
