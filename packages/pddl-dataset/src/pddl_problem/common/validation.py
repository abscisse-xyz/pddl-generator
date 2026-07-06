"""Validation helpers for command-line frontends."""

from __future__ import annotations


def positive_int(value: str) -> int:
    """Parse a strictly positive integer."""

    parsed = int(value)
    if parsed <= 0:
        raise ValueError(f"expected a positive integer, got {value!r}")
    return parsed


def parse_bool(value: str) -> bool:
    """Parse a boolean from common textual forms."""

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"expected a boolean value, got {value!r}")
