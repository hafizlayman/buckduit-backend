# =========================================
# backend/routes/predictive_fusion.py
# Stage 13.82 — Drift Memory + Confidence Decay Visualization
# =========================================
from flask import Blueprint, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os, math, random
from datetime import datetime, timedelta

load_dotenv()
fusion_bp = Blueprint("fusion_bp", __name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = None
try:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("Missing Supabase credentials")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("✅ Supabase connected – Fusion v13.82")
except Exception as e:
    print(f"❌ Supabase init failed: {e}")
    supabase = None


# =========================================
#  Helper — Confidence Decay Formula
# =========================================
def apply_confidence_decay(prev_conf: float, drift: float, decay_factor: float = 0.92) -> float:
    base = prev_conf * decay_factor
    impact = abs(drift) * 0.25
    new_val = min(max(base - impact, 0.0), 1.0)
    return round(new_val, 3)


# =========================================
#  Endpoint 1 — GET /fusion-matrix (live)
# =========================================
@fusion_bp.route("/fusion-matrix", methods=["GET"])
def get_fusion_matrix():
    try:
        now = datetime.utcnow()
        points = []
        for i in range(12):
            t = now - timedelta(minutes=i * 10)
            drift = round(random.uniform(-0.25, 0.25), 3)
            conf = round(1 - abs(drift) * 0.6, 3)
            points.append({
                "hour_label": t.strftime("%H:%M"),
                "anomaly_count": random.randint(4, 12),
                "avg_risk": round(abs(drift) * 28, 2),
                "drift_score": drift,
                "confidence_weight": conf
            })
        return jsonify({"fusion_points": list(reversed(points))}), 200
    except Exception as e:
        print(f"⚠️ Fusion matrix error: {e}")
        return jsonify({"error": "Fusion Matrix failed"}), 500


# =========================================
#  Endpoint 2 — GET /fusion-drift (real memory)
# =========================================
@fusion_bp.route("/fusion-drift", methods=["GET"])
def get_fusion_drift():
    try:
        if not supabase:
            raise Exception("Supabase unavailable")

        # fetch last record → apply decay → insert → return window
        prev_data = supabase.table("fusion_drift_memory").select("*").order("id", desc=True).limit(1).execute()
        prev = prev_data.data[0] if prev_data.data else None
        prev_conf = prev["confidence_weight"] if prev else 1.0

        drift_score = round(random.uniform(-0.25, 0.25), 3)
        conf = apply_confidence_decay(prev_conf, drift_score)
        decay = 0.92

        supabase.table("fusion_drift_memory").insert({
            "drift_score": drift_score,
            "confidence_weight": conf,
            "decay_factor": decay
        }).execute()

        window = supabase.table("fusion_drift_memory").select("*").order("id", desc=True).limit(12).execute()
        hist = list(reversed(window.data))

        return jsonify({
            "status": "success",
            "data": hist,
            "meta": {
                "latest_drift": drift_score,
                "latest_confidence": conf,
                "records": len(hist)
            }
        }), 200

    except Exception as e:
        print(f"⚠️ Fusion Drift Memory error: {e}")
        return jsonify({"error": "Fusion Drift Memory failed"}), 500
