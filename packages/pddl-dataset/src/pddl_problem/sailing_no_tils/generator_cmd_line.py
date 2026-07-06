"""Command-line interface for the sailing (no-TIL) generator."""

from __future__ import annotations

import argparse

from pddl_problem.io import emit_generated_problem

from .generator import generate_problem, render_domain_pddl
from .schema import SailingNoTilsConfig


def _parse_float_seq(value: str) -> tuple[float, ...]:
    return tuple(float(x) for x in value.split(":"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate parameterized sailing (no-TIL) PDDL instances.")
    parser.add_argument("-domain_file", dest="domain_file", default=None)
    parser.add_argument("-problem_file", dest="problem_file", default=None)
    parser.add_argument("-problem_name", dest="problem_name", default="sailing_no_tils")
    parser.add_argument("-num_boats", dest="num_boats", type=int, default=1)
    parser.add_argument("-boat_positions", dest="boat_positions", type=_parse_float_seq, default=(0.0,))
    parser.add_argument("-num_people", dest="num_people", type=int, default=1)
    parser.add_argument("-delta", dest="delta", type=float, default=6.0)
    parser.add_argument("-center_x", dest="center_x", type=float, default=0.0)
    parser.add_argument("-center_y", dest="center_y", type=float, default=0.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = SailingNoTilsConfig.model_validate(
        {k: v for k, v in vars(args).items() if k not in {"domain_file", "problem_file"}}
    )
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
