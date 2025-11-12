# ==========================================================
# backend/routes/drift_routes.py
# BuckDuit — Drift Forecast Supervisor + Telegram Notifier
# ==========================================================

from flask import Blueprint, jsonify, request
import os, random, time
import requests

drift_bp = Blueprint("drift_bp", __name__, url_prefix="/api/drift")

# Simulated in-memory drift model for testing
def compute_drift_zscore():
    return round(random.uniform(-3.0, 3.0), 2)

@drift_bp.route("/forecast", methods=["GET"])
def get_forecast():
    z = compute_drift_zscore()
    flags = {
        "alert": abs(z) > 2.0,
        "warn": abs(z) > 1.0
    }
    return jsonify({
        "zscore": z,
        "flags": flags,
        "source": "supervisor"
    }), 200


@drift_bp.route("/supervisor-ping", methods=["GET"])
def supervisor_ping():
    return jsonify({
        "status": "ok",
        "uptime": time.strftime("%Y-%m-%d %H:%M:%S"),
        "drift": {"last_z": compute_drift_zscore()}
    }), 200


@drift_bp.route("/notify-test", methods=["POST"])
def notify_test():
    data = request.get_json() or {}
    msg = data.get("msg", "BuckDuit Drift Notifier Test")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        return jsonify({"error": "Missing Telegram credentials"}), 400

    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg}

    try:
        r = requests.post(send_url, json=payload, timeout=10)
        return jsonify({
            "msg": "Notification sent" if r.ok else "Failed",
            "status": r.status_code
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
