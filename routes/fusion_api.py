# =========================================
# backend/routes/predictive_fusion.py
# Fusion Matrix — Predictive Anomaly & Risk Fusion Layer
# =========================================

from flask import Blueprint, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import random
from datetime import datetime, timedelta

# =========================================
# 1️⃣ Setup
# =========================================
load_dotenv()
fusion_bp = Blueprint("fusion_bp", __name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("✅ Supabase connected for fusion matrix")
except Exception as e:
    print(f"❌ Failed to init Supabase client: {e}")
    supabase = None

# =========================================
# 2️⃣ Helper — Mock Drift Simulation
# =========================================
def generate_fusion_data():
    now = datetime.utcnow()
    data = []

    for i in range(12):
        t = now - timedelta(minutes=i * 10)
        velocity = round(random.uniform(-0.2, 0.2), 3)
        avg_risk = round(abs(velocity) * random.uniform(10, 25), 2)
        data.append({
            "hour_label": t.strftime("%H:%M"),
            "anomaly_count": random.randint(3, 12),
            "avg_risk": avg_risk
        })
    return list(reversed(data))


# =========================================
# 3️⃣ Endpoint — Fusion Matrix API
# =========================================
@fusion_bp.route("/fusion-matrix", methods=["GET"])
def get_fusion_matrix():
    try:
        if not supabase:
            raise Exception("Supabase client unavailable")

        # Simulated fusion dataset
        anomaly_trend = generate_fusion_data()
        category_risks = [
            {"name": "Freelance", "avg": random.uniform(10, 30)},
            {"name": "Survey", "avg": random.uniform(5, 25)},
            {"name": "Gig Tasks", "avg": random.uniform(8, 35)},
            {"name": "Referral", "avg": random.uniform(3, 18)}
        ]

        return jsonify({
            "anomaly_trend": anomaly_trend,
            "category_risks": category_risks,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        print(f"⚠️ Fusion matrix fetch failed: {e}")
        return jsonify({"error": "Fusion matrix failed"}), 500
