"""Parameterized instance generator for the travel model."""

from __future__ import annotations

from pddl_problem.base import GeneratedProblem
from pddl_problem.common import make_rng, numbered_names
from pddl_problem.io import load_domain_text

from .schema import TravelConfig


def render_domain_pddl() -> str:
    """Return the static travel domain text."""

    return load_domain_text(__file__)


def generate_problem(config: TravelConfig) -> GeneratedProblem:
    """Generate one travel problem instance."""

    rng = make_rng(config.seed)
    locations = numbered_names("l", config.locations)
    edges = _make_edges(config, rng)

    init_lines = [f"    (is_at {locations[0]})", "    (= (total_travel_time) 0)"]
    for source, target, travel_time in edges:
        init_lines.append(f"    (is_connected {source} {target})")
        init_lines.append(f"    (= (travel_time {source} {target}) {travel_time})")
        if config.bidirectional:
            init_lines.append(f"    (is_connected {target} {source})")
            init_lines.append(f"    (= (travel_time {target} {source}) {travel_time})")

    objects_line = "    " + " ".join(locations) + " - location"
    init_block = "\n".join(init_lines)
    goal_location = locations[-1]
    problem_text = f"""(define (problem {config.problem_name})
 (:domain travel_domain)
 (:objects
{objects_line}
 )
 (:init
{init_block}
 )
 (:goal (and
    (is_at {goal_location})
 ))
 (:metric minimize (total_travel_time))
)
"""
    return GeneratedProblem(name=config.problem_name, domain_name="travel_domain", problem_pddl=problem_text)


def _make_edges(config: TravelConfig, rng) -> list[tuple[str, str, int]]:
    locations = numbered_names("l", config.locations)
    edges: list[tuple[str, str, int]] = []
    used_pairs: set[tuple[int, int]] = set()

    for index in range(config.locations - 1):
        pair = (index, index + 1)
        used_pairs.add(pair)
        edges.append((locations[index], locations[index + 1], _sample_travel_time(config, rng)))

    candidates = [
        (source, target)
        for source in range(config.locations - 1)
        for target in range(source + 2, config.locations)
        if (source, target) not in used_pairs
    ]
    rng.shuffle(candidates)
    for source, target in candidates[: config.extra_edges]:
        edges.append((locations[source], locations[target], _sample_travel_time(config, rng)))

    edges.sort(key=lambda item: (int(item[0][1:]), int(item[1][1:])))
    return edges


def _sample_travel_time(config: TravelConfig, rng) -> int:
    return rng.randint(config.min_travel_time, config.max_travel_time)
