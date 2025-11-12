# backend/workers/adaptive_feedback_worker.py
import os, time, requests
from utils.threshold_manager import (
    get_current_threshold, compute_new_threshold,
    write_threshold, record_adjustment
)
from services.telegram_notify import send_telegram

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:5000")  # local default
INTERVAL_MIN = int(os.getenv("ADAPTIVE_INTERVAL_MIN", "60"))

def fetch_drift_status() -> dict | None:
    # Prefer your flattened endpoints first; fall back to policy path if needed
    for path in ["/drift/status", "/api/policy/analytics/drift/status"]:
        try:
            r = requests.get(API_BASE + path, timeout=10)
            if r.ok:
                return r.json()
        except Exception:
            pass
    return None

def run_once():
    drift = fetch_drift_status()
    if not drift or drift.get("status") not in ("ok", "success"):
        send_telegram("⚠️ Adaptive Loop: no drift data available.")
        return

    z = float(drift.get("zscore", 0.0))
    drift_pct = float(drift.get("delta_pct", 0.0))
    ema = float(drift.get("ema", 0.0))
    mean = float(drift.get("mean", 0.0))
    today = float(drift.get("today", 0.0))

    prev = get_current_threshold()
    newv = compute_new_threshold(z)

    # Only write if it actually changes by >= 0.005 (noise guard)
    if abs(newv - prev) >= 0.005:
        write_threshold(newv)
        record_adjustment(z, drift_pct, ema, mean, today, prev, newv,
                          reason="auto_adjust_v2")
        send_telegram(
            f"🤖 *Adaptive AI Feedback*\n"
            f"• z-score: *{z:.2f}*  | drift: *{drift_pct:.2f}%*\n"
            f"• threshold: *{prev:.3f} → {newv:.3f}*\n"
            f"_Auto-adjusted based on recent drift_"
        )
    else:
        # quiet log
        record_adjustment(z, drift_pct, ema, mean, today, prev, prev,
                          reason="no_change_small_delta")

def main_loop():
    while True:
        try:
            run_once()
        except Exception as e:
            send_telegram(f"⚠️ Adaptive loop error: `{e}`")
        time.sleep(INTERVAL_MIN * 60)

if __name__ == "__main__":
    send_telegram("🚀 Adaptive Feedback Worker started.")
    main_loop()
