# =========================================
# backend/routes/predictive.py
# Predictive Summary & Fusion Drift Layer
# =========================================
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import random

predictive_bp = Blueprint("predictive_bp", __name__)

# ✅ Predictive Summary API
@predictive_bp.route("/summary", methods=["GET"])
def predictive_summary():
    try:
        data = {
            "total_anomalies": random.randint(30, 80),
            "risk_index": round(random.uniform(0.45, 0.89), 2),
            "uptime": f"{random.randint(97, 100)}%",
            "timestamp": datetime.utcnow().isoformat()
        }
        return jsonify(data), 200
    except Exception as e:
        print(f"⚠️ Predictive summary failed: {e}")
        return jsonify({"error": "Summary failed"}), 500


# ✅ Predictive Fusion Drift API
@predictive_bp.route("/fusion-drift", methods=["GET"])
def predictive_fusion_drift():
    try:
        now = datetime.utcnow()
        drift_data = []

        for i in range(12):
            t = now - timedelta(minutes=i * 10)
            drift_data.append({
                "timestamp": t.strftime("%H:%M"),
                "drift_score": round(random.uniform(-0.25, 0.25), 3)
            })

        return jsonify({
            "status": "success",
            "data": list(reversed(drift_data)),
            "message": "Fusion drift pattern simulated successfully"
        }), 200

    except Exception as e:
        print(f"⚠️ Fusion drift fetch failed: {e}")
        return jsonify({"error": "Fusion drift failed"}), 500
