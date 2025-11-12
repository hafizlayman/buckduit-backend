# =========================================
# backend/routes/drift_forecast.py
# Stage 13.89 — Temporal Pattern Memory Forecast API
# =========================================

from flask import Blueprint, jsonify
from supabase import create_client
import os, datetime, random

# Blueprint name must match what app.py imports
forecast_bp = Blueprint("forecast_bp", __name__)

# =========================================
# Supabase Setup
# =========================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected (drift_forecast)")
    else:
        print("⚠️ Missing Supabase credentials for drift_forecast.")
except Exception as e:
    print(f"❌ Supabase init failed (drift_forecast): {e}")

# =========================================
# Helper: Generate synthetic drift forecast data
# =========================================
def generate_forecast_data():
    now = datetime.datetime.utcnow()
    data = []
    base_drift = random.uniform(-0.1, 0.1)
    for i in range(12):  # 12 future intervals
        predicted = base_drift + random.uniform(-0.05, 0.05)
        confidence = random.uniform(0.8, 0.99)
        data.append({
            "timestamp": (now + datetime.timedelta(minutes=i * 10)).isoformat(),
            "predicted_drift": round(predicted, 3),
            "confidence": round(confidence, 3)
        })
    return data

# =========================================
# Route: /api/predictive/drift-forecast
# =========================================
@forecast_bp.route("/drift-forecast", methods=["GET"])
def get_drift_forecast():
    try:
        data = generate_forecast_data()

        if supabase:
            supabase.table("drift_forecast").insert(data).execute()

        avg_conf = sum([d["confidence"] for d in data]) / len(data)
        return jsonify({
            "status": "ok",
            "average_confidence": round(avg_conf, 3),
            "forecast_series": data
        }), 200
    except Exception as e:
        print(f"❌ Drift Forecast Error: {e}")
        return jsonify({"error": str(e)}), 500
