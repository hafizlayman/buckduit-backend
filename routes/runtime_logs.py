# =========================================
# routes/runtime_logs.py — Stage 14.02
# Read recent logs from runtime_logs
# =========================================
from flask import Blueprint, jsonify, request
from utils.supabase_client import get_supabase
from utils.decorators import log_route

runtime_bp = Blueprint("runtime_bp", __name__)

@runtime_bp.route("/runtime-logs", methods=["GET"])
@log_route("runtime_logs")
def get_runtime_logs():
    """
    Query params:
      - limit: int (default 50, max 500)
      - level: DEBUG|INFO|WARN|ERROR (optional)
      - source: str (optional exact match)
    """
    sb = get_supabase()
    if not sb:
        return jsonify({"ok": False, "error": "Supabase unavailable"}), 500

    limit = min(int(request.args.get("limit", 50)), 500)
    level = request.args.get("level")
    source = request.args.get("source")

    q = sb.table("runtime_logs").select("*").order("ts", desc=True)
    if level:
        q = q.eq("level", level)
    if source:
        q = q.eq("source", source)

    res = q.limit(limit).execute()
    return jsonify({"ok": True, "items": res.data or []})
