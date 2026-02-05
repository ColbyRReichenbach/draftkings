"""PII redaction utilities for analyst prompts and logs."""

from __future__ import annotations

import re

PII_FIELDS = {"first_name", "last_name", "email"}
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def redact_text(text: str) -> str:
    """Redact obvious PII patterns from free-form text."""
    if not text:
        return text
    redacted = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    for field in PII_FIELDS:
        redacted = re.sub(
            rf"\b{re.escape(field)}\b",
            f"[REDACTED_{field.upper()}]",
            redacted,
            flags=re.IGNORECASE,
        )
    return redacted


def find_pii_column(sql_text: str) -> str | None:
    """Return the first PII column referenced in SQL, if any."""
    lowered = sql_text.lower()
    for field in PII_FIELDS:
        if re.search(rf"\b{re.escape(field)}\b", lowered):
            return field
    return None
