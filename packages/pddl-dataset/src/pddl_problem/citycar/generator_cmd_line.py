"""Command-line interface for the CityCar generator."""

from __future__ import annotations

import argparse

from pddl_problem.common import positive_int
from pddl_problem.io import emit_generated_problem

from .generator import generate_problem, render_domain_pddl
from .schema import CityCarConfig


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for CityCar instances."""

    parser = argparse.ArgumentParser(description="Generate parameterized CityCar PDDL instances.")
    parser.add_argument("-domain_file", dest="domain_file", default=None)
    parser.add_argument("-problem_file", dest="problem_file", default=None)
    parser.add_argument("-problem_name", dest="problem_name", default="citycar")
    parser.add_argument("-rows", dest="rows", type=positive_int, default=4)
    parser.add_argument("-columns", dest="columns", type=positive_int, default=4)
    parser.add_argument("-cars", dest="cars", type=positive_int, default=3)
    parser.add_argument("-garages", dest="garages", type=positive_int, default=3)
    parser.add_argument("-roads", dest="roads", type=positive_int, default=5)
    parser.add_argument("-density", dest="density", type=float, default=1.0)
    parser.add_argument("-mode", dest="mode", default="current")
    parser.add_argument("-topology_family", dest="topology_family", default="auto")
    parser.add_argument("-seed", dest="seed", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for CityCar generation."""

    args = build_parser().parse_args(argv)
    config = CityCarConfig.model_validate(vars(args))
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
