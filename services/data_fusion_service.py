# ==========================================================
# services/data_fusion_service.py
# Stage 14.10 — Real Data Reader (Supabase)
# ==========================================================
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from supabase import Client
from utils.ai_logger import log_event

DEFAULT_VIEW = os.getenv("DRIFT_SOURCE_VIEW", "v_drift_last_180")
BIAS_VIEW    = os.getenv("BIAS_VIEW", "v_bias_window")

def _table(client: Client, name: str):
    # supabase-py treats views like tables for .table() read ops
    return client.table(name)

def get_live_series(client: Client, minutes: int = None) -> List[Dict[str, Any]]:
    minutes = minutes or int(os.getenv("REAL_WINDOW_MIN", "180"))
    since   = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    try:
        # Query the view, then filter in client side if needed
        resp = _table(client, DEFAULT_VIEW).select("*").execute()
        rows = resp.data or []
        out = []
        for r in rows:
            ts = r.get("ts")
            # supabase returns iso string; keep as-is for frontend
            out.append({
                "time": ts,
                "actual_drift": float(r.get("actual_drift") or 0),
                "predicted_drift": float(r.get("predicted_drift") or 0),
                "bias": float(r.get("bias") or 0),
            })
        log_event("INFO", "data_fusion", f"live_series rows={len(out)} from {DEFAULT_VIEW}")
        return out
    except Exception as e:
        log_event("ERROR", "data_fusion", f"get_live_series failed: {e}")
        return []

def get_bias_window(client: Client) -> Dict[str, Any]:
    try:
        resp = _table(client, BIAS_VIEW).select("*").limit(1).execute()
        row = (resp.data or [{}])[0]
        return {
            "bias_abs_max": float(row.get("bias_abs_max") or 0),
            "bias_abs_mean": float(row.get("bias_abs_mean") or 0),
            "n": int(row.get("n") or 0),
            "ts_start": row.get("ts_start"),
            "ts_end": row.get("ts_end"),
        }
    except Exception as e:
        log_event("ERROR", "data_fusion", f"get_bias_window failed: {e}")
        return {"bias_abs_max": 0, "bias_abs_mean": 0, "n": 0}
