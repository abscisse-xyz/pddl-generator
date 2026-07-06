"""Shared models for local PDDL problem generators."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GeneratedProblem:
    """Rendered problem output for one generated PDDL instance.

    Parameters
    ----------
    name:
        Problem instance name.
    domain_name:
        Referenced PDDL domain name.
    problem_pddl:
        Full rendered PDDL problem text.
    """

    name: str
    domain_name: str
    problem_pddl: str
