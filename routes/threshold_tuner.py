# =========================================
# backend/routes/threshold_tuner.py
# Stage 13.84 — Adaptive Threshold Auto-Tuner API
# =========================================

from flask import Blueprint, jsonify, request
import random
import time

tuner_bp = Blueprint("tuner_bp", __name__)

# === Simulated adaptive threshold model ===
current_thresholds = {
    "low_confidence": 0.3,
    "high_confidence": 0.7,
    "last_tuned": time.time(),
}

@tuner_bp.route("/tune-thresholds", methods=["GET", "POST"])
def tune_thresholds():
    """
    Self-adjusting threshold endpoint.
    GET  -> return current thresholds.
    POST -> simulate auto-tuning logic based on incoming metrics.
    """
    global current_thresholds

    if request.method == "POST":
        data = request.json or {}
        drift = data.get("drift", random.uniform(-0.2, 0.2))
        confidence = data.get("confidence", random.uniform(0.4, 0.9))

        # --- Simple adaptive rule ---
        if drift < -0.1:  # model instability detected
            current_thresholds["low_confidence"] = max(0.1, current_thresholds["low_confidence"] - 0.05)
        elif drift > 0.1:  # system stabilizing
            current_thresholds["high_confidence"] = min(0.95, current_thresholds["high_confidence"] + 0.05)

        current_thresholds["last_tuned"] = time.time()

        return jsonify({
            "status": "updated",
            "drift": drift,
            "confidence": confidence,
            "thresholds": current_thresholds,
        }), 200

    # === GET ===
    return jsonify({
        "status": "ok",
        "thresholds": current_thresholds,
        "last_tuned_readable": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_thresholds["last_tuned"]))
    })
