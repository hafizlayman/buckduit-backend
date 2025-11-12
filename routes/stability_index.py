# =========================================
# backend/routes/stability_index.py
# Stage 13.88 — Anomaly Density Clustering + Stability Index
# =========================================
from flask import Blueprint, jsonify
from supabase import create_client
import os, datetime, random, statistics

stability_bp = Blueprint("stability_bp", __name__)

# =========================================
# Supabase Setup
# =========================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected (stability_index)")
    else:
        print("⚠️ Missing Supabase credentials (stability_index).")
except Exception as e:
    print(f"❌ Supabase init failed (stability_index): {e}")

# =========================================
# Helper — Simulate Stability Score
# =========================================
def simulate_stability(n_points=15):
    """Simulates anomaly density and returns stability index"""
    anomalies = [random.uniform(0, 1) for _ in range(n_points)]
    density = statistics.mean(anomalies)
    volatility = statistics.pstdev(anomalies)
    stability = round(100 - (density * 60 + volatility * 40), 2)
    stability = max(min(stability, 100), 0)

    trend = "Stable"
    if stability < 40:
        trend = "Critical"
    elif stability < 70:
        trend = "Moderate"

    return stability, density, volatility, trend

# =========================================
# API Endpoint — /api/predictive/stability-index
# =========================================
@stability_bp.route("/stability-index", methods=["GET"])
def stability_index():
    try:
        score, density, vol, trend = simulate_stability()

        # Log into Supabase
        if supabase:
            supabase.table("stability_index").insert({
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "stability_score": score,
                "anomaly_density": density,
                "volatility": vol,
                "trend": trend
            }).execute()

        return jsonify({
            "status": "ok",
            "stability_score": score,
            "trend": trend,
            "anomaly_density": density,
            "volatility": vol
        }), 200
    except Exception as e:
        print(f"❌ Stability Index Error: {e}")
        return jsonify({"error": str(e)}), 500
