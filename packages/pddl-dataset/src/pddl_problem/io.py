"""I/O helpers shared by model-local generators."""

from __future__ import annotations

from pathlib import Path

from .base import GeneratedProblem


def load_domain_text(module_file: str, filename: str = "domain.pddl") -> str:
    """Load a static domain template located next to a generator module."""

    return (Path(module_file).resolve().with_name(filename)).read_text(encoding="utf-8")


def emit_generated_problem(
    problem: GeneratedProblem,
    *,
    domain_text: str,
    problem_file: str | Path | None = None,
    domain_file: str | Path | None = None,
) -> None:
    """Write generated problem/domain files or print the problem to stdout."""

    if domain_file is not None:
        Path(domain_file).write_text(domain_text, encoding="utf-8")
    if problem_file is not None:
        Path(problem_file).write_text(problem.problem_pddl, encoding="utf-8")
    else:
        print(problem.problem_pddl, end="")
