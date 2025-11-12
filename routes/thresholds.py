# =========================================
# backend/routes/thresholds.py
# =========================================
from flask import Blueprint, jsonify, request

# ✅ Consistent blueprint name
threshold_bp = Blueprint("threshold_bp", __name__)

# Simulated in-memory thresholds for testing
THRESHOLDS = {
    "risk_low": 0.3,
    "risk_medium": 0.6,
    "risk_high": 0.85,
    "auto_heal_trigger": 0.9,
}


# =========================================
# 1️⃣ Get All Thresholds
# =========================================
@threshold_bp.route("/thresholds", methods=["GET"])
def get_thresholds():
    """Return all system thresholds"""
    return jsonify({"thresholds": THRESHOLDS}), 200


# =========================================
# 2️⃣ Update a Threshold (optional admin use)
# =========================================
@threshold_bp.route("/thresholds", methods=["POST"])
def update_threshold():
    """Update specific threshold value"""
    data = request.get_json(force=True)
    key = data.get("key")
    value = data.get("value")

    if key not in THRESHOLDS:
        return jsonify({"error": f"Invalid threshold key: {key}"}), 400

    try:
        value = float(value)
    except Exception:
        return jsonify({"error": "Value must be numeric"}), 400

    THRESHOLDS[key] = value
    return jsonify({"updated": {key: value}}), 200


# =========================================
# 3️⃣ Health Check
# =========================================
@threshold_bp.route("/thresholds/health", methods=["GET"])
def thresholds_health():
    """Confirm the thresholds service is live"""
    return jsonify({"ok": True, "count": len(THRESHOLDS)}), 200
