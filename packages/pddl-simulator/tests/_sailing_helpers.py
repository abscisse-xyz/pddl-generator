"""Test-only shims preserving the legacy `generate_problem_pddl(...)` signature
on top of the migrated `pddl_problem.sailing_*` generators."""

from __future__ import annotations

from pddl_problem.sailing_no_tils.generator import generate_problem as _gen_no_tils
from pddl_problem.sailing_no_tils.schema import SailingNoTilsConfig
from pddl_problem.sailing_tils.generator import generate_problem as _gen_tils
from pddl_problem.sailing_tils.schema import SailingTilsConfig


def generate_til_problem_pddl(
    name: str, num_boats: int, boat_positions: list[float], num_people: int, delta: float
) -> str:
    return _gen_tils(
        SailingTilsConfig(
            problem_name=name,
            num_boats=num_boats,
            boat_positions=tuple(boat_positions),
            num_people=num_people,
            delta=float(delta),
        )
    ).problem_pddl


def generate_no_tils_problem_pddl(
    name: str, num_boats: int, boat_positions: list[float], num_people: int, delta: float
) -> str:
    return _gen_no_tils(
        SailingNoTilsConfig(
            problem_name=name,
            num_boats=num_boats,
            boat_positions=tuple(boat_positions),
            num_people=num_people,
            delta=float(delta),
        )
    ).problem_pddl
