# =========================================
# backend/routes/sync_alerts.py
# Stage 13.99 — Alert History + Retry + Webhook Mirror + Admin
# =========================================
from flask import Blueprint, jsonify, request
from utils.supabase_client import get_supabase
from services.sync_alert_service import send_telegram_message, retry_failed_alerts, resend_by_log_id
from services.alert_mirror_service import list_mirrors, add_mirror, set_mirror_enabled, delete_mirror

sync_alerts_bp = Blueprint("sync_alerts_bp", __name__, url_prefix="")


# -------- Telegram bridge --------
@sync_alerts_bp.post("/api/alerts/test-telegram")
def test_telegram():
    body = request.get_json(silent=True) or {}
    msg = body.get("message", "✅ Test alert from BuckDuit Sync Bridge")
    ok = send_telegram_message(msg)
    return jsonify({"ok": ok})


@sync_alerts_bp.get("/api/alerts/status")
def alert_status():
    import os
    return jsonify({
        "enabled": os.getenv("ENABLE_SYNC_ALERTS", "false").upper(),
        "threshold": os.getenv("SYNC_ALERT_THRESHOLD", "10"),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID", "(hidden)")
    })


@sync_alerts_bp.get("/api/alerts/history")
def alert_history():
    status = request.args.get("status")  # ok | failed
    limit = int(request.args.get("limit", "25"))
    sb = get_supabase()
    q = sb.table("sync_alert_log").select("*").order("created_at", desc=True).limit(limit)
    if status in ("ok", "failed"):
        q = q.eq("status", status)
    res = q.execute()
    return jsonify({"rows": res.data or []})


@sync_alerts_bp.post("/api/alerts/retry-failed")
def retry_failed():
    limit = int((request.get_json(silent=True) or {}).get("limit", 50))
    count = retry_failed_alerts(limit=limit)
    return jsonify({"ok": True, "resent": count})


@sync_alerts_bp.post("/api/alerts/resend")
def resend_alert():
    body = request.get_json(silent=True) or {}
    log_id = body.get("log_id")
    if not log_id:
        return jsonify({"ok": False, "error": "log_id required"}), 400
    ok = resend_by_log_id(log_id)
    return jsonify({"ok": ok})


# -------- Mirror Admin --------
@sync_alerts_bp.get("/api/alerts/mirrors")
def list_mirror_routes():
    return jsonify({"rows": list_mirrors()})


@sync_alerts_bp.post("/api/alerts/mirrors")
def add_mirror_route():
    body = request.get_json(silent=True) or {}
    url = body.get("url")
    if not url:
        return jsonify({"ok": False, "error": "url required"}), 400
    row = add_mirror(url)
    return jsonify({"ok": True, "row": row})


@sync_alerts_bp.patch("/api/alerts/mirrors/<mid>")
def toggle_mirror_route(mid):
    body = request.get_json(silent=True) or {}
    enabled = bool(body.get("enabled", True))
    row = set_mirror_enabled(mid, enabled)
    return jsonify({"ok": True, "row": row})


@sync_alerts_bp.delete("/api/alerts/mirrors/<mid>")
def delete_mirror_route(mid):
    delete_mirror(mid)
    return jsonify({"ok": True})
