# =========================================
# backend/routes/predictive_heatmap.py
# Stage 13.85 — Adaptive Drift Heatmap API
# =========================================

from flask import Blueprint, jsonify
from supabase import create_client
import os
import random
import datetime

heatmap_bp = Blueprint("heatmap_bp", __name__)

# =========================================
# Supabase Setup
# =========================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected (heatmap_bp)")
    else:
        print("⚠️ Missing Supabase credentials (heatmap_bp).")
except Exception as e:
    print(f"❌ Supabase init failed (heatmap_bp): {e}")


# =========================================
# Helper: generate synthetic heatmap if no data
# =========================================
def generate_heatmap_data():
    """Return mock heatmap data structure if Supabase table is empty."""
    hours = [f"{h:02d}:00" for h in range(24)]
    categories = ["Freelance", "Surveys", "Gigs", "Microtasks", "Investing"]
    data = []

    for hour in hours:
        row = {"hour_label": hour}
        for cat in categories:
            # random confidence drift matrix (0.7–0.99)
            row[cat] = round(random.uniform(0.7, 0.99), 3)
        data.append(row)
    return data


# =========================================
# Route: /api/predictive/drift-heatmap
# =========================================
@heatmap_bp.route("/drift-heatmap", methods=["GET"])
def get_drift_heatmap():
    """
    Return hourly drift confidence grid.
    Attempts to fetch from Supabase 'fused_risks',
    else generates synthetic placeholder data.
    """
    try:
        if supabase:
            response = supabase.table("fused_risks").select("*").execute()
            rows = response.data or []
            if len(rows) > 0:
                formatted = []
                for r in rows:
                    formatted.append({
                        "hour_label": r.get("hour_label"),
                        "Freelance": r.get("avg_risk"),
                        "Surveys": r.get("anomaly_count"),
                        "Gigs": r.get("avg_risk"),
                        "Microtasks": r.get("anomaly_count"),
                        "Investing": r.get("avg_risk")
                    })
                return jsonify({"status": "success", "heatmap": formatted}), 200

        # fallback mock if no Supabase or no rows
        mock = generate_heatmap_data()
        return jsonify({"status": "mock", "heatmap": mock}), 200

    except Exception as e:
        print(f"❌ Heatmap route error: {e}")
        return jsonify({"error": str(e)}), 500


# =========================================
# Route: /api/predictive/heatmap-status
# (Optional quick diagnostic)
# =========================================
@heatmap_bp.route("/heatmap-status", methods=["GET"])
def heatmap_status():
    return jsonify({
        "message": "Drift Heatmap API online",
        "timestamp": datetime.datetime.utcnow().isoformat()
    })
