"""Command-line interface for the travel generator."""

from __future__ import annotations

import argparse

from pddl_problem.common import parse_bool, positive_int
from pddl_problem.io import emit_generated_problem

from .generator import generate_problem, render_domain_pddl
from .schema import TravelConfig


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for travel instances."""

    parser = argparse.ArgumentParser(description="Generate parameterized travel PDDL instances.")
    parser.add_argument("-domain_file", dest="domain_file", default=None)
    parser.add_argument("-problem_file", dest="problem_file", default=None)
    parser.add_argument("-problem_name", dest="problem_name", default="travel")
    parser.add_argument("-locations", dest="locations", type=positive_int, default=5)
    parser.add_argument("-extra_edges", dest="extra_edges", type=int, default=2)
    parser.add_argument("-min_travel_time", dest="min_travel_time", type=positive_int, default=20)
    parser.add_argument("-max_travel_time", dest="max_travel_time", type=positive_int, default=120)
    parser.add_argument("-bidirectional", dest="bidirectional", type=parse_bool, default=False)
    parser.add_argument("-seed", dest="seed", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for travel generation."""

    args = build_parser().parse_args(argv)
    config = TravelConfig.model_validate(vars(args))
    problem = generate_problem(config)
    emit_generated_problem(
        problem,
        domain_text=render_domain_pddl(),
        problem_file=args.problem_file,
        domain_file=args.domain_file,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
