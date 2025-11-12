# ==========================================================
# Adaptive Trend (gradient & direction) — mock
# ==========================================================
from flask import Blueprint, jsonify
import random

adaptivetrend_bp = Blueprint("adaptivetrend_bp", __name__)

@adaptivetrend_bp.route("/adaptive-trend", methods=["GET"])
def adaptive_trend():
    gradient = round(random.uniform(-0.12, 0.12), 3)
    direction = "up" if gradient > 0.02 else ("down" if gradient < -0.02 else "flat")
    confidence = round(random.uniform(0.6, 0.95), 2)
    return jsonify({
        "ok": True,
        "gradient": gradient,
        "direction": direction,
        "confidence": confidence
    })
