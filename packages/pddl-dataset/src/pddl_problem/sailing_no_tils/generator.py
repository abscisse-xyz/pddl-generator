"""Sailing temporal-PDDL problem generator (no-TIL variant)."""

from __future__ import annotations

import math

from pddl_problem.base import GeneratedProblem
from pddl_problem.io import load_domain_text

from .schema import SailingNoTilsConfig

DOMAIN_NAME = "sailing"


def render_domain_pddl() -> str:
    return load_domain_text(__file__)


def generate_problem(config: SailingNoTilsConfig) -> GeneratedProblem:
    boat_names = [f"b{i}" for i in range(config.num_boats)]
    person_names = [f"p{i}" for i in range(config.num_people)]
    init_atoms = ["\t\t(still_alive)"]

    for i, boat_name in enumerate(boat_names):
        init_atoms.append(f"\t\t(idle {boat_name})")
        init_atoms.append(f"\t\t(= (x {boat_name}) {int(config.boat_positions[i])})")
        init_atoms.append(f"\t\t(= (y {boat_name}) 0)")

    angle_step = 360.0 / config.num_people if config.num_people > 0 else 0.0
    for i, person_name in enumerate(person_names):
        radius = (i + 1) * config.delta
        _angle_rad = math.radians(i * angle_step)
        _px = config.center_x + radius * math.cos(_angle_rad)
        _py = config.center_y + radius * math.sin(_angle_rad)
        init_atoms.append(f"\t\t(= (d {person_name}) {int(radius)})")

    deadline = round(config.delta * config.num_people * 2, 0)
    init_atoms.append(f"\t\t(= (deadline) {int(deadline)})")
    init_block = "\n".join(init_atoms)

    goal_inner = "\n\t\t\t".join(f"(saved {person_name})" for person_name in person_names)
    goal_block = f"""\t(:goal
\t\t(and
\t\t\t{goal_inner}
\t\t)
\t)
"""

    objects_lines = []
    if boat_names:
        objects_lines.append(f"\t\t{' '.join(boat_names)}  - boat")
    if person_names:
        objects_lines.append(f"\t\t{' '.join(person_names)}  - person")
    objects_block = "\n".join(objects_lines)

    problem_pddl = f"""(define (problem {config.problem_name})

\t(:domain {DOMAIN_NAME})

\t(:objects
{objects_block}
\t)

  \t(:init
{init_block}
\t)

{goal_block}
\t(:metric minimize (total-time))
)
"""
    return GeneratedProblem(name=config.problem_name, domain_name=DOMAIN_NAME, problem_pddl=problem_pddl)
