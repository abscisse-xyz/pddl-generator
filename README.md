# pddl-generator

Tools for working with PDDL: a benchmark dataset generator (62 domains), a
temporal simulator with persistent traces, and a unified CLI dispatcher
(`pddl-cli`).

## Layout

```
pddl-cli/                  Top-level CLI dispatcher (this is the user-facing app)
packages/
  pddl-dataset/            Registry-driven wrapper around AI-Planning/pddl-generators
  pddl-simulator/          Temporal PDDL simulator + DuckDB-backed trace store
Dockerfile                 Multi-stage build for the whole project
```

`pddl-cli` is the only intended entry point. It dispatches to:
- `pddl-cli dataset …` — generate domain + problem instances
- `pddl-cli generate batch …` — generate curated multi-instance batches
- `pddl-cli simulate …` — auto-plan and replay a problem; persist the trace
- `pddl-cli plan …` — placeholder; planning-only output (future)

## Build the container

```sh
docker buildx build --platform linux/amd64 -t pddl-cli:dev .
```

The image clones `AI-Planning/pddl-generators`, compiles the C/C++/flex/bison
generators in a builder stage, then installs `pddl-dataset`, `pddl-simulator`,
and `pddl-cli` into a Python 3.13 runtime with a JRE for the ENHSP planner.
The Dockerfile also defaults its base images to `linux/amd64`, so builds from
Apple Silicon hosts do not silently fall back to `linux/arm64`.

### Planner availability and platform

Planner availability depends on the **target architecture of the Python
environment where `unified-planning` is installed**, not on Docker by itself.
Some planner plugins ship native binaries only for selected platforms, while
**ENHSP** is JVM-based and therefore much more portable.

In this repo:

- `linux/amd64` images install `unified-planning` with `enhsp`, `aries`,
  `fast-downward`, and `fmap`.
- `linux/arm64` installs only `enhsp`, because the other packaged planner
  artifacts are not available there.

That is why planner coverage inside Docker changes with platform: if Docker
builds an `arm64` image on an Apple Silicon host, the dependency resolver sees
`linux/arm64` and installs the reduced planner set. By basing the image on
`linux/amd64`, the container gets the broader planner set consistently, even
when it is built from macOS/arm64 via emulation.

**Practical consequence**: temporal-PDDL `simulate` is expected to work in the
default `linux/amd64` image, but can fail in a `linux/arm64` override build if
no installed planner supports `CONTINUOUS_TIME`.

## Usage

The image's `ENTRYPOINT` is `pddl-cli`, so flags after the image name are
parsed by the dispatcher.

### List subcommands

```sh
docker run --rm pddl-cli:dev --help
```

### Dataset generation

```sh
# List the 62 registered domains
docker run --rm pddl-cli:dev dataset --list

# Describe a domain's parameters
docker run --rm pddl-cli:dev dataset cavediving --describe

# Generate a problem instance with default params
docker run --rm -v "$PWD/out:/work" pddl-cli:dev dataset gripper --out gripper

# Generate three instances at varied parameters
docker run --rm -v "$PWD/out:/work" pddl-cli:dev dataset gripper \
    -p balls=10 --count 3 --seed-base 42 --out gripper-large

# Generate CityCar with a specific generator mode
docker run --rm -v "$PWD/out:/work" pddl-cli:dev dataset citycar \
    -p mode=topology-first -p cars=4 -p garages=3 -p roads=5 --out citycar-topology

# Get just the domain.pddl
docker run --rm -v "$PWD/out:/work" pddl-cli:dev dataset gripper --domain-only --out gripper
```

CityCar supports three generator modes via `-p mode=...`:

- `current` — density-style generation compatible with the previous parameter
  shape.
- `topology-first` — small grids with mixed pressure profiles such as balanced,
  car-pressure, road-rich, garage-rich, junction-tight, and junction-open.
  Batch instances vary cars, garages, roads, and junction counts independently,
  including unused garages that are not goal junctions.
- `solution-first` — builds a valid route skeleton first,
  then adds topology around it so the emitted problem has a constructive
  solvability certificate.

### Curated batch generation

For domains with a curated batch plan, use `generate batch`. This runs the
normal dataset generator loop inside the app, with per-instance parameters
derived from the batch policy. Batch generation also accepts `-p NAME=VALUE`
overrides; for CityCar this is the recommended way to select
`mode=topology-first` or `mode=solution-first`.

```sh
# List supported batch domains
docker run --rm pddl-cli:dev generate batch --list

# Generate a 200-instance citycar batch
docker run --rm -v "$PWD/out:/work" pddl-cli:dev \
    generate batch citycar --out /work/citycar --count 200 --seed-base 1

# Generate CityCar's small topology-first variant
docker run --rm -v "$PWD/out:/work" pddl-cli:dev \
    generate batch citycar --out /work/citycar-topology --count 200 --seed-base 1 -p mode=topology-first

# Generate CityCar's small solution-first variant
docker run --rm -v "$PWD/out:/work" pddl-cli:dev \
    generate batch citycar --out /work/citycar-solution --count 200 --seed-base 1 -p mode=solution-first
```

Currently supported batch domains are `cavediving`, `citycar`, `schedule`, and
`travel`.

For the full registry/parameter docs, see
[packages/pddl-dataset/README.md](packages/pddl-dataset/README.md).

### Simulation

`pddl-cli simulate` is designed to consume the exact directory layout emitted
by `pddl-cli dataset`: one `domain.pddl` plus either one or more `pNN.pddl`
files or a single `problem.pddl`. In Docker, the normal pipeline is:

1. bind-mount a host workspace into `/work`
2. run `pddl-cli dataset ... --out /work/...`
3. run `pddl-cli simulate --input /work/... --out /work/...`

Use the same mounted host directory for both commands so the generated dataset
is visible to the later simulation step.

```sh
mkdir -p "$PWD/out"

# 1. Generate a temporal dataset inside the mounted workspace.
docker run --rm \
  -v "$PWD/out:/work" \
  pddl-cli:dev \
  dataset sailing-tils --out /work/sailing

# 2. Simulate from that dataset directory into a second output directory.
docker run --rm \
  -v "$PWD/out:/work" \
  pddl-cli:dev \
  simulate --input /work/sailing --out /work/sailing-sim

# 3. Inspect one problem result on the host.
cat ./out/sailing-sim/p01/manifest.json
```

`pddl-cli simulate` auto-plans each problem via `OneshotPlanner`, replays the
plan against the simulator, and writes per-problem traces plus a session-level
state-store database. Planning is executed inline in the simulator process;
the simulator lazily grounds only the actions that appear in the returned plan.
Use `--jobs N` to solve and replay multiple problems in parallel; session DB
writes are still serialized by the parent process so DuckDB/SQLite output stays
deterministic.

`./out/sailing-sim/` contains:
- `simulation.duckdb` — **session-level** state store; one row in
  `simulation_runs` per problem, joined back to `state_snapshots`,
  `action_events`, and `trace_entries` via `run_id`. All problems in one
  invocation share this DB.
- `manifest.json` — top-level aggregate (per-problem `goals_satisfied`, etc.)
- `p01/`, `p02/`, … — one subdirectory per problem with:
  - `domain.pddl` + `pNN.pddl` — echoed from input for self-contained replay
  - `trace.json` — ordered event log
  - `plan.txt` — best-effort human-readable plan
  - `manifest.json` — per-problem metadata (planner, plan_topology, run_id, …)

`simulate` expects a full dataset directory, not just `domain.pddl`. If you
generated a domain with `dataset --domain-only`, you must later pair it with a
problem file before simulation.

#### Simulate flags

```
--input DIR              Required. Dataset-style directory (domain.pddl + pNN.pddl).
--out DIR                Output directory (default: ./out).
--planner NAME           Specific UP planner; default auto-selects via OneshotPlanner.
--planner-timeout SEC    Planner timeout in seconds; default 60 when supported
                         by the selected UP engine.
--persist-backend X      duckdb (default) | sqlite | none.
--export-parquet         After persistence, emit snapshots.parquet + trace.parquet
                         per problem (DuckDB only).
--max-steps N            Hard cap on simulation steps per problem.
--jobs N                 Number of problems to solve/simulate in parallel.
--rerun-timeouts         Rerun only problems marked TIMEOUT/timed_out in a
                         previous simulation manifest.
--rerun-from PATH        Previous simulation directory or manifest.json for
                         --rerun-timeouts (default: --out).
```

#### Querying the trace

DuckDB ships native `LIST<STRUCT(...)>` columns, so you can query the
simulation database directly without parsing JSON:

```python
import duckdb
con = duckdb.connect("out/sailing-sim/simulation.duckdb")
# Trajectory across every problem in this session, joined to its problem name
con.execute("""
    SELECT r.problem_name, s.step_index, s.sim_time, len(s.facts) AS fact_count
    FROM state_snapshots s
    JOIN simulation_runs r ON r.id = s.run_id
    ORDER BY r.id, s.step_index
""").fetchall()
```

For model training, the database also exposes `state_action_transitions`,
which joins each executed action to the snapshot before and after it:

```sql
SELECT problem_name, step_index, action_name, arguments,
       state_facts, state_numeric_values,
       next_state_facts, next_state_numeric_values
FROM state_action_transitions t
JOIN simulation_runs r ON r.id = t.run_id
ORDER BY r.id, step_index;
```

For batch-export to ML pipelines, `--export-parquet` writes the same data
in columnar Parquet, readable by any pandas/polars/spark consumer.

#### DuckDB query templates via Docker

You can inspect a simulation database with the same `pddl-cli:dev` image. Set
`SIM_DB` to the database under the mounted `/work` directory; for example,
`/work/citycar-sim/simulation.duckdb`.

```sh
docker run --rm -i \
  -v "$PWD/out:/work" \
  --entrypoint python \
  -e SIM_DB=/work/citycar-sim/simulation.duckdb \
  -e RUN_ID=1 \
  -e STEP_INDEX=1 \
  pddl-cli:dev - <<'PY'
import os
from pprint import pprint
import duckdb

con = duckdb.connect(os.environ["SIM_DB"], read_only=True)
rows = con.execute(
    """
    SELECT r.problem_name, s.step_index, s.sim_time, len(s.facts) AS fact_count
    FROM state_snapshots s
    JOIN simulation_runs r ON r.id = s.run_id
    ORDER BY r.id, s.step_index
    """
).fetchall()

for row in rows:
  pprint(row)
PY
```

```sh
docker run --rm -i \
  -v "$PWD/out:/work" \
  --entrypoint python \
  -e SIM_DB=/work/citycar-sim/simulation.duckdb \
  pddl-cli:dev - <<'PY'
import os
import duckdb

con = duckdb.connect(os.environ["SIM_DB"], read_only=True)

queries = {
    "tables": """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
    """,
    "runs": """
        SELECT id, domain_name, problem_name, created_at
        FROM simulation_runs
        ORDER BY id
    """,
    "planner attempts": """
        SELECT problem_name, planner_name, status, failure_stage,
               timed_out, plan_topology
        FROM planner_attempts
        ORDER BY id
    """,
    "executed actions": """
        SELECT step_index, sim_time, phase, action_name, arguments
        FROM action_events
        ORDER BY run_id, step_index
    """,
    "state snapshots": """
        SELECT run_id, step_index, sim_time, reason,
               len(facts) AS fact_count,
               len(numeric_values) AS numeric_count,
               len(running_actions) AS running_count
        FROM state_snapshots
        ORDER BY run_id, step_index
    """,
    "state action transitions": """
        SELECT run_id, step_index, action_name, arguments,
               len(state_facts) AS facts_before,
               len(next_state_facts) AS facts_after
        FROM state_action_transitions
        ORDER BY run_id, step_index
    """,
}

for name, sql in queries.items():
    print(f"\n-- {name}")
    for row in con.execute(sql).fetchall():
        print(row)
PY
```

To inspect one full `(state, action, next_state)` transition:

```sh
docker run --rm -i \
  -v "$PWD/out:/work" \
  --entrypoint python \
  -e SIM_DB=/work/citycar-sim/simulation.duckdb \
  -e RUN_ID=1 \
  -e STEP_INDEX=1 \
  pddl-cli:dev - <<'PY'
import os
from pprint import pprint
import duckdb

con = duckdb.connect(os.environ["SIM_DB"], read_only=True)
row = con.execute(
    """
    SELECT run_id, step_index, sim_time,
           action_name, arguments,
           state_facts, state_numeric_values, state_running_actions,
           next_state_facts, next_state_numeric_values, next_state_running_actions
    FROM state_action_transitions
    WHERE run_id = ? AND step_index = ?
    """,
    [int(os.environ["RUN_ID"]), int(os.environ["STEP_INDEX"])],
).fetchone()
pprint(row)
PY
```

For a training dataset where every row contains the previous full state, the
executed action, and the next full state, join `action_events` to the snapshot
at the same `step_index` and the snapshot immediately before it:

```sh
docker run --rm -i \
  -v "$PWD/out:/work" \
  --entrypoint python \
  -e SIM_DB=/work/citycar-sim/simulation.duckdb \
  pddl-cli:dev - <<'PY'
import os
from pprint import pprint
import duckdb

con = duckdb.connect(os.environ["SIM_DB"], read_only=True)
rows = con.execute(
    """
    SELECT
        r.problem_name,
        a.run_id,
        a.step_index,
        a.sim_time AS action_time,
        a.phase AS action_phase,
        a.action_name,
        a.arguments AS action_parameters,
        a.duration AS action_duration,

        prev.sim_time AS previous_state_time,
        prev.reason AS previous_state_reason,
        prev.facts AS previous_state_facts,
        prev.numeric_values AS previous_state_numeric_values,
        prev.running_actions AS previous_state_running_actions,
        prev.pending_events AS previous_state_pending_events,

        next.sim_time AS next_state_time,
        next.reason AS next_state_reason,
        next.facts AS next_state_facts,
        next.numeric_values AS next_state_numeric_values,
        next.running_actions AS next_state_running_actions,
        next.pending_events AS next_state_pending_events
    FROM action_events a
    JOIN simulation_runs r
      ON r.id = a.run_id
    JOIN state_snapshots next
      ON next.run_id = a.run_id
     AND next.step_index = a.step_index
    JOIN state_snapshots prev
      ON prev.run_id = a.run_id
     AND prev.step_index = a.step_index - 1
    ORDER BY a.run_id, a.step_index
    """
).fetchall()

for row in rows:
    pprint(row)
PY
```

## Development

```sh
uv sync --all-packages --group dev
uv run pytest packages/pddl-simulator/tests packages/pddl-dataset/tests pddl-cli/tests
uv run pddl-cli dataset --list
```

Real upstream generator binaries are only exercised inside Docker — the
C/C++/flex/bison generators are not built on the host.
