# ==========================================================
# Stability Index — mock
# ==========================================================
from flask import Blueprint, jsonify
import random, math

stabilityindex_bp = Blueprint("stabilityindex_bp", __name__)

@stabilityindex_bp.route("/stability-index", methods=["GET"])
def stability_index():
    stability = round(random.uniform(55, 85), 2)  # %
    anomaly_density = round(random.uniform(0.25, 0.55), 3)
    volatility = round(random.uniform(0.18, 0.38), 3)
    bucket = "Moderate" if stability < 70 else "Good"
    return jsonify({
        "ok": True,
        "stability_score": stability,
        "bucket": bucket,
        "anomaly_density": anomaly_density,
        "volatility": volatility
    })
