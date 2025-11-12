# backend/routes/alerts_test_push.py
from flask import Blueprint, jsonify
from monitor.telegram_sender import send_telegram_message

bp_alerts_test = Blueprint("alerts_test_push", __name__)

@bp_alerts_test.route("/api/alerts/notify-test", methods=["POST", "GET"])
def alerts_notify_test():
    try:
        send_telegram_message("✅ BuckDuit alert test — wiring OK.")
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
