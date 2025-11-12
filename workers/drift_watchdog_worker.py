# backend/workers/drift_watchdog_worker.py
import os, time, traceback
from datetime import datetime, timezone
from dotenv import load_dotenv

def _detect_env():
    flag = os.getenv("APP_ENV", "").lower()
    if flag in ("prod", "production"):
        return ".env.prod"
    if flag in ("stage", "staging"):
        return ".env.stage"
    return ".env.dev"

load_dotenv(_detect_env())

from services.utils.ai_logger import log_event
from services.supa_client import get_supabase

SUPABASE = get_supabase()
CHECK_INTERVAL = int(os.getenv("WATCHDOG_INTERVAL_SECONDS", "120"))
BIAS_THRESHOLD = float(os.getenv("BIAS_THRESHOLD", "0.12"))
ALERTS_TABLE = os.getenv("PREDICTIVE_ALERTS_TABLE", "predictive_alerts")

def _utc_now(): return datetime.now(timezone.utc).isoformat()

def _latest_bias_abs_max():
    # assumes you created v_bias_window view (Stage 14.10)
    try:
        resp = SUPABASE.table("bias_window").select("*").order("ts_end", desc=True).limit(1).execute()
    except Exception:
        # if you kept it as VIEW v_bias_window, switch to .from_('v_bias_window')
        resp = SUPABASE.from_("v_bias_window").select("*").order("ts_end", desc=True).limit(1).execute()
    rows = resp.data or []
    if not rows: return 0.0
    return float(rows[0].get("bias_abs_max", 0.0))

def run_once():
    try:
        bam = _latest_bias_abs_max()
        flagged = bam > BIAS_THRESHOLD
        if flagged:
            SUPABASE.table(ALERTS_TABLE).insert({
                "timestamp": _utc_now(),
                "message": f"Bias exceeded threshold ({bam:.3f} > {BIAS_THRESHOLD:.3f})",
                "bias_max": bam,
                "threshold": BIAS_THRESHOLD,
                "flagged": True
            }).execute()
            log_event("WARN", "watchdog", f"bias breach {bam:.3f} > {BIAS_THRESHOLD:.3f}")
        else:
            log_event("INFO", "watchdog", f"bias ok {bam:.3f} ≤ {BIAS_THRESHOLD:.3f}")
        return True
    except Exception as e:
        log_event("ERROR", "watchdog", f"check failed: {e}", {"trace": traceback.format_exc(limit=1)})
        return False

def main_loop():
    log_event("INFO", "worker_boot", f"watchdog starting (interval={CHECK_INTERVAL}s)")
    while True:
        run_once()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
