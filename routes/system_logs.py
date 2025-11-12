# =========================================
# backend/routes/system_logs.py
# =========================================
from flask import Blueprint, jsonify, request
import datetime

# Create blueprint
logs_bp = Blueprint("logs_bp", __name__)

# Temporary in-memory logs (for local testing)
system_logs = [
    {
        "id": 1,
        "timestamp": str(datetime.datetime.utcnow()),
        "severity": "info",
        "message": "System initialized successfully",
    },
    {
        "id": 2,
        "timestamp": str(datetime.datetime.utcnow()),
        "severity": "warning",
        "message": "Predictive service response slower than expected",
    },
    {
        "id": 3,
        "timestamp": str(datetime.datetime.utcnow()),
        "severity": "error",
        "message": "Temporary Supabase connection issue",
    },
]


# =========================================
# 1️⃣ Fetch All Logs
# =========================================
@logs_bp.route("/logs", methods=["GET"])
def get_logs():
    """Return all system logs"""
    return jsonify({"logs": system_logs}), 200


# =========================================
# 2️⃣ Add a New Log Entry (for testing)
# =========================================
@logs_bp.route("/logs", methods=["POST"])
def add_log():
    """Add a log entry manually (optional)"""
    data = request.get_json(force=True)
    new_log = {
        "id": len(system_logs) + 1,
        "timestamp": str(datetime.datetime.utcnow()),
        "severity": data.get("severity", "info"),
        "message": data.get("message", "No message provided"),
    }
    system_logs.append(new_log)
    return jsonify({"added": new_log}), 201


# =========================================
# 3️⃣ Health Endpoint for Logs
# =========================================
@logs_bp.route("/logs/health", methods=["GET"])
def logs_health():
    """Simple check to confirm log system working"""
    return jsonify({"ok": True, "count": len(system_logs)}), 200
