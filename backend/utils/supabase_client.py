from __future__ import annotations

import os
import logging
from typing import Any, Dict

try:
    from supabase import create_client, Client
except Exception:  # pragma: no cover - optional dependency
    create_client = None  # type: ignore
    Client = None  # type: ignore

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or create_client is None:
    logger.warning("Supabase not configured or client not installed; supabase writes disabled")
    sb: Client | None = None
else:
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)


def insert_audit(entry: Dict[str, Any]) -> None:
    """Insert an audit entry into Supabase table `rg_audit_trail`.

    This is best-effort and will not raise on failure; failures are logged.
    """
    if sb is None:
        logger.debug("Supabase client not initialized; skipping audit insert")
        return

    try:
        resp = sb.table("rg_audit_trail").insert(entry).execute()
        # client returns a response-like object with `.error` on failure
        if getattr(resp, "error", None):
            logger.error("Supabase insert error: %s", resp.error)
    except Exception:  # pragma: no cover - runtime guard
        logger.exception("Failed to write audit entry to Supabase")
