# travel

This model generator emits parameterized instances for a simple travel domain.

Supported parameters:
- `locations`
- `extra_edges`
- `min_travel_time`
- `max_travel_time`
- `bidirectional`
- `seed`

Example:

```bash
python -m pddl_problem.travel.generator_cmd_line \
  -problem_file problem.pddl \
  -domain_file domain.pddl \
  -problem_name travel_01 \
  -locations 6 \
  -extra_edges 3 \
  -seed 7
```
