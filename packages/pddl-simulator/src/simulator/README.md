# Querying the simulator state store

`pddl-cli simulate` writes **one DuckDB database per session**
(`<out>/simulation.duckdb`). All problems processed in that invocation share
the database; each problem gets its own `simulation_runs` row, with
`state_snapshots`, `action_events`, and `trace_entries` joined by `run_id`.
Below are reference query patterns for the common downstream needs.

## Schema

```
simulation_runs(id, domain_name, problem_name, created_at)
state_snapshots(
    id, run_id, step_index, sim_time,    -- sim_time is "num/den" text for exactness
    reason,                              -- reset | action_start | action_end | timed_effect | time_advance
    facts:           STRUCT(name, arguments[])[],
    numeric_values:  STRUCT(name, arguments[], value)[],
    running_actions: STRUCT(name, arguments[], started_at, ends_at)[],
    pending_events:  STRUCT(time, priority, kind, description)[]
)
trace_entries(id, run_id, step_index, sim_time, kind, description)
action_events(id, run_id, step_index, sim_time, phase, action_name,
              action_kind, arguments, duration)
state_action_transitions(run_id, step_index, sim_time, phase, action_name,
                         action_kind, arguments, duration,
                         state_facts, state_numeric_values,
                         state_running_actions, next_state_facts,
                         next_state_numeric_values, next_state_running_actions)
```

`facts`, `numeric_values`, etc. are **native** lists of structs — no JSON
parsing required.

## Pattern 1 — point-in-time state lookup

"What was the state at simulation time 1.5?"

```python
import duckdb
from fractions import Fraction
con = duckdb.connect("simulation.duckdb")

# DuckDB doesn't natively understand Fraction; convert to text comparison.
target = "3/2"  # = 1.5
row = con.execute("""
    SELECT step_index, sim_time, reason, facts, numeric_values
    FROM state_snapshots
    WHERE run_id = ?
      AND CAST(SPLIT_PART(sim_time, '/', 1) AS DOUBLE)
        / CAST(SPLIT_PART(sim_time, '/', 2) AS DOUBLE) <= 1.5
    ORDER BY step_index DESC
    LIMIT 1
""", [run_id]).fetchone()
```

Or use the Protocol method directly:

```python
from simulator import DuckDBStateStore
store = DuckDBStateStore("simulation.duckdb")
snapshot = store.load_snapshot_at_or_before(run_id, Fraction(3, 2))
```

## Pattern 2 — sample state/action transitions for ML

"Stream the executed `(state, action, next_state)` rows for a run."

```sql
SELECT step_index,
       action_name,
       arguments,
       state_facts,
       state_numeric_values,
       next_state_facts,
       next_state_numeric_values
FROM state_action_transitions
WHERE run_id = ?
ORDER BY step_index
```

## Pattern 3 — sample state snapshots for ML

"Stream all (state, time) tuples for runs 1..N at stride 5."

```python
from simulator import DuckDBStateStore
store = DuckDBStateStore("simulation.duckdb")
for snapshot in store.iter_snapshots(run_id=1, stride=5):
    yield snapshot.sim_time, snapshot.state
```

For batch work, prefer `--export-parquet` and load via polars or pandas:

```python
import polars as pl
df = pl.read_parquet("snapshots.parquet")
# native columns — project without parsing JSON:
df.select(["sim_time", "reason", "facts"])
```

## Pattern 4 — analytical aggregation across snapshots

"How does fact count evolve over time, across every problem in this session?"

```sql
SELECT r.problem_name,
       s.step_index,
       s.sim_time,
       len(s.facts) AS fact_count,
       len(s.numeric_values) AS fluent_count,
       len(s.running_actions) AS in_flight
FROM state_snapshots s
JOIN simulation_runs r ON r.id = s.run_id
ORDER BY r.id, s.step_index
```

These queries don't touch JSON text — column projection runs at native scan
speed.
