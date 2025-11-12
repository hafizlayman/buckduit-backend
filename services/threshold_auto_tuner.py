# =========================================
# backend/services/threshold_auto_tuner.py
# Stage 13.84 — Adaptive Threshold Auto-Tuner
# =========================================
import statistics
import datetime
from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def calculate_dynamic_threshold():
    """Recalculate adaptive thresholds based on drift and confidence patterns."""
    try:
        result = supabase.table("fusion_drift_memory").select("*").order("timestamp", desc=True).limit(50).execute()
        rows = result.data or []
        if not rows:
            print("⚠️ No drift data found — cannot tune thresholds.")
            return None

        drifts = [float(r.get("drift_score", 0)) for r in rows]
        confs = [float(r.get("confidence_weight", 0)) for r in rows]

        avg_drift = round(statistics.mean(drifts), 4)
        std_drift = round(statistics.pstdev(drifts), 4)
        avg_conf = round(statistics.mean(confs), 4)
        std_conf = round(statistics.pstdev(confs), 4)

        # Adaptive logic
        new_upper = min(1.0, avg_conf + std_conf * 0.8)
        new_lower = max(0.0, avg_conf - std_conf * 1.2)
        new_drift_alert = round(abs(avg_drift) + std_drift * 1.5, 4)

        threshold_record = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "avg_confidence": avg_conf,
            "avg_drift": avg_drift,
            "upper_threshold": new_upper,
            "lower_threshold": new_lower,
            "drift_alert_threshold": new_drift_alert,
        }

        # Save to table
        supabase.table("adaptive_thresholds").insert(threshold_record).execute()

        print(f"✅ Auto-tuned thresholds saved — conf range {new_lower:.2f}-{new_upper:.2f}, drift alert {new_drift_alert}")
        return threshold_record

    except Exception as e:
        print(f"❌ Threshold tuning failed: {e}")
        return None
