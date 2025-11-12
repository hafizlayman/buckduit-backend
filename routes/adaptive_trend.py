# =========================================
# backend/routes/adaptive_trend.py
# Stage 13.92 — Auto-Weight Calibration Engine v1
# =========================================
from flask import Blueprint, jsonify
from supabase import create_client
import os
from datetime import datetime

adaptive_trend_bp = Blueprint("adaptive_trend_bp", __name__)

# ---------- Supabase client ----------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected (adaptive_trend)")
    else:
        print("⚠️ Missing Supabase credentials (adaptive_trend).")
except Exception as e:
    print(f"❌ Supabase init failed (adaptive_trend): {e}")


def _safe_float(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


# ---------- API: /api/predictive/adaptive-trend ----------
@adaptive_trend_bp.route("/adaptive-trend", methods=["GET"])
def adaptive_trend():
    """
    Returns the last 24 rows from adaptive_learning_metrics
    plus light smoothing & min/max for front-end scaling.
    """
    try:
        if not supabase:
            return jsonify({"error": "Supabase not initialized"}), 500

        # Pull latest 24 points (most recent first)
        resp = (
            supabase.table("adaptive_learning_metrics")
            .select("*")
            .order("timestamp", desc=True)
            .limit(24)
            .execute()
        )

        rows = resp.data or []

        # Normalize + chronological order for charts
        series = []
        for r in reversed(rows):
            series.append({
                "timestamp": r.get("timestamp"),
                "accuracy": _safe_float(r.get("avg_accuracy")),
                "drift_bias": _safe_float(r.get("drift_bias")),
                "correction_weight": _safe_float(r.get("correction_weight")),
                "learning_rate": _safe_float(r.get("learning_rate")),
            })

        # Simple smoothing (3-point moving average) for accuracy only
        smoothed_acc = []
        window = 3
        for i in range(len(series)):
            window_vals = [series[j]["accuracy"] for j in range(max(0, i - window + 1), i + 1)]
            smoothed_acc.append(round(sum(window_vals) / max(1, len(window_vals)), 4))

        # Attach smoothed accuracy
        for i, row in enumerate(series):
            row["accuracy_smooth"] = smoothed_acc[i]

        # Compute min/max for client scaling
        def mm(key):
            vals = [row[key] for row in series] or [0]
            return {"min": min(vals), "max": max(vals)}

        meta = {
            "accuracy": mm("accuracy"),
            "accuracy_smooth": mm("accuracy_smooth"),
            "drift_bias": mm("drift_bias"),
            "correction_weight": mm("correction_weight"),
            "learning_rate": mm("learning_rate"),
            "count": len(series),
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

        return jsonify({"status": "ok", "meta": meta, "series": series}), 200

    except Exception as e:
        print(f"❌ adaptive_trend error: {e}")
        return jsonify({"error": str(e)}), 500
