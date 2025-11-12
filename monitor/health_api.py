# ============================================
# health_api.py — Health Monitoring Blueprint
# ============================================
from flask import Blueprint, jsonify
import os, json

health_blueprint = Blueprint("health_blueprint", __name__)

@health_blueprint.route("/status", methods=["GET"])
def get_health_status():
    """Return current backend health status."""
    health_path = os.path.join("backend", "data", "health_status.json")

    if not os.path.exists(health_path):
        return jsonify({"status": "unknown"}), 200

    try:
        with open(health_path, "r") as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"status": f"error: {e}"}), 500
