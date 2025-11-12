# backend/routes/alerts_detail.py
from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
from monitor.supa_client import get_supabase

bp_alerts_detail = Blueprint("alerts_detail", __name__)

@bp_alerts_detail.get("/api/alerts/<int:alert_id>")
def get_alert(alert_id: int):
    """
    Return a single alert by id from alerts_view (normalized fields).
    """
    supa = get_supabase()
    try:
        resp = supa.table("alerts_view").select("*").eq("id", alert_id).limit(1).execute()
        rows = resp.data or []
        if not rows:
            return jsonify({"ok": False, "error": "Not found"}), 404
        row = rows[0]
        # normalize keys your UI expects
        return jsonify({
            "ok": True,
            "item": {
                "id": row.get("id"),
                "created_at": row.get("created_at"),
                "severity": (row.get("severity") or "").upper(),
                "source": row.get("source"),
                "category": row.get("category"),
                "message": row.get("message"),
                "meta": row.get("meta") or {},
            }
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@bp_alerts_detail.post("/api/alerts/retry")
def retry_alert():
    """
    Lightweight 'retry' action:
    - Accepts JSON: { "id": <alert_id> }
    - Inserts a new system_logs row noting the retry (ties back via meta.retry_of)
    """
    body = request.get_json(silent=True) or {}
    alert_id = body.get("id")
    if not alert_id:
        return jsonify({"ok": False, "error": "id required"}), 400

    supa = get_supabase()
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        # Try to fetch the original alert to copy useful fields
        original = supa.table("alerts_view").select("*").eq("id", alert_id).limit(1).execute()
        base = (original.data or [{}])[0]

        details = f"Retry triggered for alert #{alert_id}"
        meta = base.get("meta") or {}
        meta["retry_of"] = alert_id
        meta["action"] = "retry"

        insert = supa.table("system_logs").insert({
            "timestamp": now_iso,
            "severity": "INFO",
            "ai_signal": base.get("source") or "UI",
            "event_type": "RETRY",
            "details": details,
            "meta": meta
        }).execute()

        return jsonify({"ok": True, "inserted": insert.data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
