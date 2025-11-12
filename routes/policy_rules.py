# =========================================
# backend/routes/policy_rules.py
# =========================================
from flask import Blueprint, jsonify

policy_bp = Blueprint("policy_bp", __name__)

@policy_bp.route("/rules", methods=["GET"])
def get_policy_rules():
    """
    Placeholder endpoint for policy rules
    You can extend this later with real database logic.
    """
    rules = [
        {"id": 1, "name": "Auto-Heal Trigger", "status": "active"},
        {"id": 2, "name": "Drift Anomaly Flag", "status": "active"},
        {"id": 3, "name": "Threshold Decay", "status": "standby"}
    ]
    return jsonify({"rules": rules})
