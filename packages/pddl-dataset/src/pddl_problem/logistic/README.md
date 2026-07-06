# logistic

This model generator emits parameterized instances for a lightweight logistic domain.

Supported parameters:
- `locations`
- `robots`
- `packages`
- `min_distance`
- `max_distance`
- `min_velocity`
- `max_velocity`
- `seed`

Example:

```bash
python -m pddl_problem.logistic.generator_cmd_line \
  -problem_file problem.pddl \
  -domain_file domain.pddl \
  -problem_name logistic_01 \
  -locations 5 \
  -robots 3 \
  -packages 4 \
  -seed 11
```
