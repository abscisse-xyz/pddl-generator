"""Naming helpers."""

from __future__ import annotations


def numbered_names(prefix: str, count: int, *, start: int = 1) -> list[str]:
    """Return ``prefix`` names like ``l1, l2, ..., ln``."""

    return [f"{prefix}{index}" for index in range(start, start + count)]
