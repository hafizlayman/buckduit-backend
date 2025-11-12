# =========================================
# backend/routes/data_fusion.py
# Stage 13.84 — Data Fusion Integration (Corrected)
# =========================================
from flask import Blueprint, jsonify
from supabase import create_client
import os

# =========================================
# Supabase Client Setup
# =========================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized (data_fusion)")
    else:
        print("❌ Missing Supabase credentials.")
except Exception as e:
    print(f"❌ Supabase init failed (data_fusion): {e}")

# =========================================
# Blueprint Declaration
# =========================================
datafusion_bp = Blueprint("datafusion_bp", __name__)  # ✅ FIXED NAME

# =========================================
# ROUTE 1 — Fusion Drift
# =========================================
@datafusion_bp.route("/fusion-drift", methods=["GET"])
def get_fusion_drift():
    """Fetch drift + confidence metrics."""
    try:
        result = supabase.table("fusion_drift_memory").select("*").order("timestamp", desc=True).limit(50).execute()
        data = result.data or []
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        print(f"❌ Error fetching fusion_drift: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================================
# ROUTE 2 — Fusion Matrix
# =========================================
@datafusion_bp.route("/fusion-matrix", methods=["GET"])
def get_fusion_matrix():
    """Aggregate drift and confidence data hourly."""
    try:
        result = supabase.table("fusion_drift_memory").select("*").execute()
        rows = result.data or []
        if not rows:
            return jsonify({"status": "ok", "fusion_points": []}), 200

        hourly = {}
        for r in rows:
            ts = r.get("timestamp")
            if not ts:
                continue
            hour = ts[:13]  # e.g. "2025-11-09T14"
            if hour not in hourly:
                hourly[hour] = {"count": 0, "drift_sum": 0.0, "conf_sum": 0.0}
            hourly[hour]["count"] += 1
            hourly[hour]["drift_sum"] += float(r.get("drift_score", 0))
            hourly[hour]["conf_sum"] += float(r.get("confidence_weight", 0))

        fusion_points = []
        for h, v in hourly.items():
            fusion_points.append({
                "hour_label": h,
                "drift_score": round(v["drift_sum"] / v["count"], 4),
                "confidence_weight": round(v["conf_sum"] / v["count"], 4)
            })

        fusion_points.sort(key=lambda x: x["hour_label"])
        return jsonify({"status": "success", "fusion_points": fusion_points}), 200

    except Exception as e:
        print(f"❌ Error building fusion_matrix: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================================
# ROUTE 3 — Fusion Latest Snapshot
# =========================================
@datafusion_bp.route("/fusion-latest", methods=["GET"])
def get_fusion_latest():
    """Return the most recent fusion snapshot."""
    try:
        result = supabase.table("fusion_drift_memory").select("*").order("timestamp", desc=True).limit(1).execute()
        latest = result.data[0] if result.data else {}
        return jsonify({"status": "success", "latest": latest}), 200
    except Exception as e:
        print(f"❌ Error fetching fusion_latest: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
