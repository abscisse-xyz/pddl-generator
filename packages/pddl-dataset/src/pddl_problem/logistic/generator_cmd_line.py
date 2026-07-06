"""Command-line interface for the logistic generator."""

from __future__ import annotations

import argparse

from pddl_problem.common import positive_int
from pddl_problem.io import emit_generated_problem

from .generator import generate_problem, render_domain_pddl
from .schema import LogisticConfig


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for logistic instances."""

    parser = argparse.ArgumentParser(description="Generate parameterized logistic PDDL instances.")
    parser.add_argument("-domain_file", dest="domain_file", default=None)
    parser.add_argument("-problem_file", dest="problem_file", default=None)
    parser.add_argument("-problem_name", dest="problem_name", default="logistic")
    parser.add_argument("-locations", dest="locations", type=positive_int, default=4)
    parser.add_argument("-robots", dest="robots", type=positive_int, default=2)
    parser.add_argument("-packages", dest="packages", type=positive_int, default=2)
    parser.add_argument("-min_distance", dest="min_distance", type=positive_int, default=5)
    parser.add_argument("-max_distance", dest="max_distance", type=positive_int, default=12)
    parser.add_argument("-min_velocity", dest="min_velocity", type=positive_int, default=1)
    parser.add_argument("-max_velocity", dest="max_velocity", type=positive_int, default=2)
    parser.add_argument("-seed", dest="seed", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for logistic generation."""

    args = build_parser().parse_args(argv)
    config = LogisticConfig.model_validate(vars(args))
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
