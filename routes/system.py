# backend/routes/system.py
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timezone

system_bp = Blueprint("system_bp", __name__)

@system_bp.route("/health")
def health():
    return jsonify({"ok": True, "message": "System operational and responding correctly", "ts": datetime.now(timezone.utc).isoformat()})

@system_bp.route("/recent-alerts")
def recent_alerts():
    """
    Returns last guardrail alerts. If Supabase present and table 'predictive_alerts' exists,
    it tries to read. Otherwise returns mock alerts.
    """
    supabase = getattr(current_app, "supabase", None)
    limit = int(request.args.get("limit", 5))
    try:
        if supabase:
            resp = supabase.table("predictive_alerts").select("*").order("timestamp", desc=True).limit(limit).execute()
            rows = resp.data or []
            return jsonify({"ok": True, "items": rows})
    except Exception:
        pass  # fall back to mock

    mock = [
        {
            "id": 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Bias exceeded soft threshold (+0.13) in last 30 mins",
            "bias_max": 0.13,
            "threshold": 0.12,
            "flagged": True
        },
        {
            "id": 2,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Drift slope rising; smoothing active",
            "bias_max": 0.07,
            "threshold": 0.12,
            "flagged": False
        }
    ]
    return jsonify({"ok": True, "items": mock})

@system_bp.route("/runtime-logs")
def runtime_logs():
    # lightweight mock so your Diagnostics table shows content
    limit = int(request.args.get("limit", 50))
    now = datetime.now(timezone.utc).isoformat()
    sample = [
        {"id": i, "ts": now, "level": "INFO", "source": "runtime_logs", "message": f"mock log #{i}"}
        for i in range(limit)
    ]
    return jsonify({"ok": True, "items": sample})
