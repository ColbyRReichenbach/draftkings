"""Snowflake SQL validation helpers."""

from __future__ import annotations

import re

_SNOWFLAKE_PROHIBITED = [
    re.compile(r"::"),
    re.compile(r"\bINTERVAL\b", re.IGNORECASE),
    re.compile(r"\bDATE_SUB\b", re.IGNORECASE),
    re.compile(r"\bREGEXP_MATCH\b", re.IGNORECASE),
    re.compile(r"\bIFNULL\b", re.IGNORECASE),
]


def validate_snowflake_sql(sql: str) -> list[str]:
    """Return a list of violations for non-Snowflake syntax."""
    violations: list[str] = []
    for pattern in _SNOWFLAKE_PROHIBITED:
        if pattern.search(sql):
            violations.append(f"Prohibited syntax detected: {pattern.pattern}")
    return violations
