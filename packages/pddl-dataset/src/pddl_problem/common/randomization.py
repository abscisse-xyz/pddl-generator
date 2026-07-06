"""Randomness helpers."""

from __future__ import annotations

import random


def make_rng(seed: int | None) -> random.Random:
    """Create a dedicated RNG for deterministic instance generation."""

    return random.Random(seed)
