# =========================================
# backend/routes/adaptive_trend.py
# Stage 13.92 — Adaptive Trend API (Fix)
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


@adaptive_trend_bp.route("/adaptive-trend", methods=["GET"])
def adaptive_trend():
    """Return last 24 adaptive learning records."""
    try:
        if not supabase:
            return jsonify({"error": "Supabase not initialized"}), 500

        response = (
            supabase.table("adaptive_learning_metrics")
            .select("*")
            .order("timestamp", desc=True)
            .limit(24)
            .execute()
        )

        rows = response.data or []
        rows.reverse()  # chronological order

        series = []
        for r in rows:
            series.append({
                "timestamp": r.get("timestamp"),
                "accuracy": float(r.get("avg_accuracy") or 0),
                "drift_bias": float(r.get("drift_bias") or 0),
                "correction_weight": float(r.get("correction_weight") or 0),
                "learning_rate": float(r.get("learning_rate") or 0),
            })

        meta = {
            "count": len(series),
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }

        return jsonify({"status": "ok", "series": series, "meta": meta})

    except Exception as e:
        print(f"❌ adaptive_trend error: {e}")
        return jsonify({"error": str(e)}), 500
