"""Parameterized instance generator for the logistic model."""

from __future__ import annotations

from pddl_problem.base import GeneratedProblem
from pddl_problem.common import make_rng, numbered_names
from pddl_problem.io import load_domain_text

from .schema import LogisticConfig


def render_domain_pddl() -> str:
    """Return the static logistic domain text."""

    return load_domain_text(__file__)


def generate_problem(config: LogisticConfig) -> GeneratedProblem:
    """Generate one logistic problem instance."""

    rng = make_rng(config.seed)
    locations = numbered_names("l", config.locations)
    robots = numbered_names("r", config.robots)
    packages = numbered_names("p", config.packages)
    edges = _make_edges(config, rng)
    velocities = {robot: rng.randint(config.min_velocity, config.max_velocity) for robot in robots}

    object_lines = [
        "    " + " ".join(locations) + " - location",
        "    " + " ".join(robots) + " - robot",
        "    " + " ".join(packages) + " - package",
    ]

    init_lines: list[str] = []
    start_location = locations[0]
    goal_location = locations[-1]
    for robot in robots:
        init_lines.append(f"    (robot_at {robot} {start_location})")
        init_lines.append(f"    (robot_free {robot})")
        init_lines.append(f"    (= (velocity {robot}) {velocities[robot]})")
    for package in packages:
        init_lines.append(f"    (package_at {package} {start_location})")
    for source, target, distance in edges:
        init_lines.append(f"    (is_connected {source} {target})")
        init_lines.append(f"    (is_connected {target} {source})")
        init_lines.append(f"    (= (distance {source} {target}) {distance})")
        init_lines.append(f"    (= (distance {target} {source}) {distance})")

    goal_lines = [f"    (package_at {package} {goal_location})" for package in packages]
    objects_block = "\n".join(object_lines)
    init_block = "\n".join(init_lines)
    goal_block = "\n".join(goal_lines)

    problem_text = f"""(define (problem {config.problem_name})
 (:domain logistic_domain)
 (:objects
{objects_block}
 )
 (:init
{init_block}
 )
 (:goal (and
{goal_block}
 ))
)
"""
    return GeneratedProblem(name=config.problem_name, domain_name="logistic_domain", problem_pddl=problem_text)


def _make_edges(config: LogisticConfig, rng) -> list[tuple[str, str, int]]:
    locations = numbered_names("l", config.locations)
    return [
        (locations[index], locations[index + 1], rng.randint(config.min_distance, config.max_distance))
        for index in range(config.locations - 1)
    ]
