# =========================================
# backend/routes/drift_memory.py
# Stage 13.86 — Gradient Analyzer + Drift Memory
# =========================================
from flask import Blueprint, jsonify
from supabase import create_client
import os
import datetime
import random

memory_bp = Blueprint("memory_bp", __name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected (drift_memory)")
    else:
        print("⚠️ Missing Supabase credentials (drift_memory).")
except Exception as e:
    print(f"❌ Supabase init failed (drift_memory): {e}")

# =========================================
# Helper: compute gradient direction
# =========================================
def detect_gradient(series):
    if len(series) < 2:
        return "flat"
    slope = series[-1] - series[-2]
    if slope > 0.01:
        return "rising"
    elif slope < -0.01:
        return "falling"
    else:
        return "stable"

# =========================================
# Route: /api/predictive/drift-memory
# =========================================
@memory_bp.route("/drift-memory", methods=["GET"])
def drift_memory():
    """Simulate drift gradient analysis and store anomalies."""
    try:
        # Generate mock drift values for simulation
        now = datetime.datetime.utcnow()
        drift_series = [round(random.uniform(-0.25, 0.25), 3) for _ in range(10)]
        avg_risk = round(sum(abs(x) for x in drift_series) / len(drift_series), 3)
        gradient = detect_gradient(drift_series)

        # store synthetic anomaly snapshot
        if supabase:
            supabase.table("drift_memory").insert({
                "timestamp": now.isoformat(),
                "avg_risk": avg_risk,
                "gradient": gradient,
                "recent_drift": drift_series[-1],
            }).execute()

        result = {
            "gradient": gradient,
            "average_risk": avg_risk,
            "recent_drift": drift_series[-1],
            "series": drift_series,
            "stored": bool(supabase)
        }
        return jsonify(result), 200

    except Exception as e:
        print(f"❌ Drift Memory Error: {e}")
        return jsonify({"error": str(e)}), 500
