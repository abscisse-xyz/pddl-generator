from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pddl_dataset.runner import BatchInstanceSpec


@dataclass(frozen=True)
class BatchSpec:
    domain: str
    default_count: int
    plan: dict[str, Any]
    derive: Callable[[int, int, int], BatchInstanceSpec]
    derive_with_params: Callable[[int, int, int, dict[str, Any]], BatchInstanceSpec] | None = None


def build_instance(params_with_family: dict[str, Any]) -> BatchInstanceSpec:
    params = dict(params_with_family)
    family = params.pop("family", None)
    raw_seed = params.get("seed")
    seed = raw_seed if isinstance(raw_seed, int) else None
    return BatchInstanceSpec(params=params, family=str(family) if family is not None else None, seed=seed)


def interp_int(start: int, end: int, progress: float) -> int:
    return round(start + (end - start) * progress)
