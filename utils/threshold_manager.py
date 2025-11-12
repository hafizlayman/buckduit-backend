# backend/utils/threshold_manager.py
import os
from datetime import datetime, timezone
from utils.supa_client import supabase

BASE_CONF = float(os.getenv("BASE_CONFIDENCE", "0.80"))
ADJUST_PER_Z = float(os.getenv("ADJUST_PER_ZSCORE", "0.02"))
MIN_CONF = float(os.getenv("MIN_CONFIDENCE", "0.70"))
MAX_CONF = float(os.getenv("MAX_CONFIDENCE", "0.90"))

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def get_current_threshold() -> float:
    # Single-row table (id=1)
    r = supabase.table("rule_settings").select("confidence_threshold").eq("id", 1).execute()
    if r.data and len(r.data) > 0 and r.data[0].get("confidence_threshold") is not None:
        return float(r.data[0]["confidence_threshold"])
    return BASE_CONF

def compute_new_threshold(zscore: float) -> float:
    """
    Positive zscore => loosen threshold slightly (higher conf target) to avoid over-triggering
    Negative zscore => tighten a bit (lower conf target)
    Feel free to invert sign if you want the opposite; this mapping is conservative.
    """
    delta = zscore * ADJUST_PER_Z
    candidate = BASE_CONF + delta
    return _clamp(candidate, MIN_CONF, MAX_CONF)

def write_threshold(new_threshold: float):
    supabase.table("rule_settings").update({
        "confidence_threshold": new_threshold,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", 1).execute()

def record_adjustment(zscore: float, drift_pct: float, ema: float, mean: float, today: float,
                      previous: float, new_value: float, reason: str):
    supabase.table("adaptive_thresholds").insert({
        "zscore": zscore,
        "drift_pct": drift_pct,
        "ema": ema,
        "mean": mean,
        "today": today,
        "previous_threshold": previous,
        "new_threshold": new_value,
        "reason": reason
    }).execute()
