# backend/monitor/adaptive_sync.py
from __future__ import annotations
import os
from datetime import datetime, timezone
from supabase import create_client
from typing import Dict, Any
from config.ai_runtime import update_params_from_row, get_params

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

def _client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Supabase credentials missing for worker sync")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def pull_latest_state() -> Dict[str, Any]:
    """
    Reads the most-recent row from auto_tuner_state (single-row table by design)
    and returns it. If empty, returns {}.
    """
    sb = _client()
    res = sb.table("auto_tuner_state").select("*").order("updated_at", desc=True).limit(1).execute()
    rows = res.data or []
    return rows[0] if rows else {}

def apply_to_runtime(source: str = "manual_push") -> Dict[str, Any]:
    """
    Pulls tuner values from DB, applies to in-memory runtime config,
    and writes an audit row to worker_sync_log.
    """
    sb = _client()
    row = pull_latest_state()
    applied = update_params_from_row(row)

    sb.table("worker_sync_log").insert({
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": source,
        "target_accuracy": applied.get("target_accuracy"),
        "max_bias": applied.get("max_bias"),
        "learning_rate": applied.get("learning_rate"),
        "correction_weight": applied.get("correction_weight"),
        "notes": f"Applied via {source}",
    }).execute()
    return applied

def current_params() -> Dict[str, Any]:
    return get_params()
