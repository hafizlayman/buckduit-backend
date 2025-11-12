from flask import Blueprint, jsonify
import random, datetime

# ✅ define blueprint with proper prefix
predictive_narrative_bp = Blueprint("predictive_narrative", __name__, url_prefix="/api/predictive")

@predictive_narrative_bp.route("/narrative", methods=["GET"])
def get_narrative():
    # Generate mock AI narrative values
    confidence_change = round(random.uniform(-0.05, 0.05), 2)
    anomaly_prob = random.randint(5, 25)
    trend = "improving" if confidence_change > 0 else "declining"
    mood = "stable" if anomaly_prob < 15 else "volatile"

    summary = (
        f"Forecast indicates {trend} stability this week. "
        f"Confidence changed by {confidence_change * 100:+.1f}%, "
        f"with anomaly probability near {anomaly_prob}% — system remains {mood}."
    )

    return jsonify({
        "status": "ok",
        "summary": summary,
        "trend": trend,
        "confidence_delta": confidence_change,
        "anomaly_probability": anomaly_prob,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    })
