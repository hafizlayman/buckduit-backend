# =========================================
# backend/routes/drift_comparison.py
# Stage 13.90 — AI Drift Forecast Comparison (Actual vs Predicted Overlay)
# =========================================

from flask import Blueprint, jsonify
from supabase import create_client
import os, datetime, random

comparison_bp = Blueprint("comparison_bp", __name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected (drift_comparison)")
    else:
        print("⚠️ Missing Supabase credentials (drift_comparison).")
except Exception as e:
    print(f"❌ Supabase init failed (drift_comparison): {e}")

# =========================================
# Helper: Generate Synthetic Comparison Data
# =========================================
def generate_comparison():
    now = datetime.datetime.utcnow()
    data = []
    base_drift = random.uniform(-0.2, 0.2)
    base_conf = random.uniform(0.85, 0.98)

    for i in range(8):
        actual_drift = base_drift + random.uniform(-0.05, 0.05)
        predicted_drift = actual_drift + random.uniform(-0.03, 0.03)
        accuracy = 1 - abs(predicted_drift - actual_drift)
        data.append({
            "timestamp": (now + datetime.timedelta(minutes=i * 5)).isoformat(),
            "actual_drift": round(actual_drift, 3),
            "predicted_drift": round(predicted_drift, 3),
            "accuracy": round(accuracy, 3)
        })
    return data

# =========================================
# API Route: /api/predictive/drift-comparison
# =========================================
@comparison_bp.route("/drift-comparison", methods=["GET"])
def drift_comparison():
    try:
        data = generate_comparison()

        if supabase:
            supabase.table("drift_comparison").insert(data).execute()

        avg_accuracy = sum([d["accuracy"] for d in data]) / len(data)

        return jsonify({
            "status": "ok",
            "average_accuracy": round(avg_accuracy, 3),
            "comparison_series": data
        }), 200
    except Exception as e:
        print(f"❌ Drift Comparison Error: {e}")
        return jsonify({"error": str(e)}), 500
