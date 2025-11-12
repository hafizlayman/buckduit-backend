# backend/routes/predictive_forecast.py
from flask import Blueprint, jsonify
import random, datetime

# ✅ Correct Blueprint definition
predictive_forecast_bp = Blueprint("predictive_forecast", __name__)

@predictive_forecast_bp.route("/api/predictive/forecast", methods=["GET"])
def get_forecast():
    today = datetime.date.today()
    forecast_data = []
    base_conf = 0.8
    base_risk = 0.4

    for i in range(7):
        day = today + datetime.timedelta(days=i + 1)
        confidence = max(0, min(1, base_conf + random.uniform(-0.05, 0.05)))
        risk_score = max(0, min(1, base_risk + random.uniform(-0.08, 0.08)))
        anomaly = abs(confidence - risk_score) > 0.4
        forecast_data.append({
            "date": str(day),
            "confidence": round(confidence, 2),
            "risk_score": round(risk_score, 2),
            "anomaly": anomaly
        })

    return jsonify({
        "status": "ok",
        "forecast": forecast_data
    })
