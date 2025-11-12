# backend/routes/alerts.py
from flask import Blueprint, jsonify, request
import os
from supabase import create_client
from utils.ai_logger import log_event

alerts_bp = Blueprint("alerts", __name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

_client = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        log_event("INFO", "alerts_api", "Supabase connected")
except Exception as e:
    log_event("ERROR", "alerts_api", f"Supabase connect failed: {e}")

@alerts_bp.route("/recent", methods=["GET"])
def recent_alerts():
    limit = int(request.args.get("limit", "10"))
    if not _client:
        return jsonify({"ok": True, "items": [], "note": "no supabase (mock only)"}), 200
    try:
        res = _client.table("predictive_alerts").select("*").order("timestamp", desc=True).limit(limit).execute()
        items = res.data or []
        return jsonify({"ok": True, "items": items})
    except Exception as e:
        log_event("ERROR", "alerts_api", f"recent failed: {e}")
        return jsonify({"ok": False, "error": "recent failed"}), 500

@alerts_bp.route("/test", methods=["POST"])
def test_alert():
    # quick button to force a flagged alert
    if not _client:
        return jsonify({"ok": False, "error": "supabase missing"}), 500
    try:
        payload = {
            "message": "Manual test alert (flagged)",
            "bias_max": 0.222,
            "threshold": float(os.getenv("ALERT_BASE_THRESHOLD", "0.12")),
            "flagged": True
        }
        _client.table("predictive_alerts").insert(payload).execute()
        log_event("INFO", "alerts_api", "test alert inserted")
        return jsonify({"ok": True})
    except Exception as e:
        log_event("ERROR", "alerts_api", f"test insert failed: {e}")
        return jsonify({"ok": False}), 500
