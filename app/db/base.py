"""Helpers for working with asyncpg Record objects."""
from typing import Any


def record_to_dict(record) -> dict[str, Any] | None:
    """Convert an asyncpg Record to a plain dict, or return None."""
    if record is None:
        return None
    return dict(record)


def records_to_list(records) -> list[dict[str, Any]]:
    """Convert a list of asyncpg Records to a list of dicts."""
    return [dict(r) for r in records]


def build_placeholders(n: int, start: int = 1) -> str:
    """Return '$1, $2, ..., $n' positional placeholder string."""
    return ", ".join(f"${i}" for i in range(start, start + n))
