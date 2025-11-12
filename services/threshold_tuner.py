# =========================================
# backend/routes/threshold_tuner.py
# Stage 13.84 — Adaptive Threshold API
# =========================================
from flask import Blueprint, jsonify
from services.threshold_auto_tuner import calculate_dynamic_threshold

tuner_bp = Blueprint("tuner_bp", __name__)

@tuner_bp.route("/tune-thresholds", methods=["GET"])
def tune_thresholds():
    """Trigger auto-tuning process manually (or via frontend refresh)."""
    record = calculate_dynamic_threshold()
    if record:
        return jsonify({"status": "success", "data": record}), 200
    else:
        return jsonify({"status": "error", "message": "Auto-tuning failed"}), 500
