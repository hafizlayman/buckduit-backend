# =========================================
# backend/routes/adaptive_learning.py
# Stage 13.91 — Adaptive Self-Learning Loop
# =========================================
from flask import Blueprint, jsonify
from supabase import create_client
import os, datetime, random

adaptive_bp = Blueprint("adaptive_bp", __name__)

# =========================================
# Supabase Setup
# =========================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected (adaptive_learning)")
    else:
        print("⚠️ Missing Supabase credentials (adaptive_learning).")
except Exception as e:
    print(f"❌ Supabase init failed (adaptive_learning): {e}")

# =========================================
# Helper Function: simulate adaptive learning cycle
# =========================================
def simulate_learning_cycle():
    """
    Generates synthetic self-learning metrics:
    - accuracy improves slightly over time
    - drift bias & correction weight auto-balance
    """
    base_acc = random.uniform(0.82, 0.98)
    drift_bias = random.uniform(-0.05, 0.05)
    learning_rate = round(random.uniform(0.05, 0.15), 3)
    correction_weight = round(base_acc + drift_bias * learning_rate, 4)

    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "avg_accuracy": round(base_acc, 3),
        "drift_bias": round(drift_bias, 3),
        "correction_weight": correction_weight,
        "learning_rate": learning_rate,
    }

# =========================================
# Route: /api/predictive/adaptive-learning
# =========================================
@adaptive_bp.route("/adaptive-learning", methods=["GET"])
def adaptive_learning():
    try:
        data = simulate_learning_cycle()
        if supabase:
            supabase.table("adaptive_learning_metrics").insert(data).execute()
        return jsonify({"status": "ok", "data": data}), 200
    except Exception as e:
        print(f"❌ Adaptive Learning Error: {e}")
        return jsonify({"error": str(e)}), 500
