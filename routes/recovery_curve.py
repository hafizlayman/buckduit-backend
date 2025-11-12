# =========================================
# backend/routes/recovery_curve.py
# Stage 13.87 — Predictive Recovery Curve + Volatility Overlay
# =========================================
from flask import Blueprint, jsonify
from supabase import create_client
import os, datetime, random, math

recovery_bp = Blueprint("recovery_bp", __name__)

# =========================================
# Supabase Setup
# =========================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected (recovery_curve)")
    else:
        print("⚠️ Missing Supabase credentials (recovery_curve).")
except Exception as e:
    print(f"❌ Supabase init failed (recovery_curve): {e}")

# =========================================
# Helper: Simulate drift decay and volatility
# =========================================
def simulate_decay(base_confidence=0.85, steps=12):
    """Generates synthetic decay recovery data"""
    series = []
    drift = random.uniform(-0.3, 0.3)
    volatility = random.uniform(0.01, 0.05)
    now = datetime.datetime.utcnow()

    for i in range(steps):
        t = i / steps
        confidence = base_confidence + (1 - math.exp(-4 * t)) * (1 - base_confidence)
        confidence = round(confidence - random.uniform(0, volatility), 3)
        series.append({
            "timestamp": (now + datetime.timedelta(minutes=i * 5)).isoformat(),
            "drift_level": round(drift * (1 - t), 3),
            "confidence": max(min(confidence, 1.0), 0),
            "volatility": round(volatility, 3),
        })

    return series, volatility

# =========================================
# Route: /api/predictive/recovery-curve
# =========================================
@recovery_bp.route("/recovery-curve", methods=["GET"])
def recovery_curve():
    try:
        data, vol = simulate_decay()
        avg_conf = round(sum(d["confidence"] for d in data) / len(data), 3)

        if supabase:
            supabase.table("recovery_metrics").insert({
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "avg_confidence": avg_conf,
                "avg_volatility": vol,
                "data_points": len(data)
            }).execute()

        return jsonify({
            "status": "ok",
            "average_confidence": avg_conf,
            "average_volatility": vol,
            "series": data
        }), 200
    except Exception as e:
        print(f"❌ Recovery Curve Error: {e}")
        return jsonify({"error": str(e)}), 500
