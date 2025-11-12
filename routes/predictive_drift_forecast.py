# ==========================================================
# Predictive Drift Forecast API — Stage 14.04
# ==========================================================
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import random

driftforecast_bp = Blueprint("driftforecast_bp", __name__)

@driftforecast_bp.route("/drift-forecast", methods=["GET"])
def drift_forecast():
    """Simulate drift forecast points for testing."""
    now = datetime.utcnow()
    data = []
    for i in range(10):
        t = (now - timedelta(minutes=(9 - i) * 5)).isoformat()
        actual = round(random.uniform(-0.2, 0.1), 3)
        predicted = actual + round(random.uniform(-0.02, 0.02), 3)
        data.append({
            "time": t,
            "actual_drift": actual,
            "predicted_drift": predicted
        })
    return jsonify({
        "ok": True,
        "data": data,
        "avg_accuracy": 98.6
    })
