# =========================================
# backend/routes/sync_admin.py
# Stage 13.96 — Live Source Sync Admin API
# =========================================
from flask import Blueprint, jsonify, request
import os
from utils.supabase_client import get_supabase

sync_admin_bp = Blueprint("sync_admin_bp", __name__, url_prefix="/api/sync")

# GET /api/sync/config
@sync_admin_bp.get("/config")
def get_config():
    return jsonify({
        "source_mode": os.getenv("SYNC_SOURCE_MODE", "mock"),
        "source_table": os.getenv("SYNC_SOURCE_TABLE", "offers_source"),
        "target_table": os.getenv("SYNC_TARGET_TABLE", "offers"),
        "status_table": os.getenv("SYNC_STATUS_TABLE", "sync_status"),
        "deltas_table": os.getenv("SYNC_DELTAS_TABLE", "sync_deltas"),
        "interval_seconds": int(os.getenv("SYNC_INTERVAL_SECONDS", "60"))
    })

# GET /api/sync/export?table=offers
@sync_admin_bp.get("/export")
def export_table():
    table = request.args.get("table", os.getenv("SYNC_TARGET_TABLE", "offers"))
    sb = get_supabase()
    res = sb.table(table).select("*").limit(50000).execute()
    return jsonify({"table": table, "rows": res.data or []})

# POST /api/sync/import
# body: { "rows": [ { "id": "...", "name": "...", ... }, ... ] }
@sync_admin_bp.post("/import")
def import_rows():
    table = os.getenv("SYNC_SOURCE_TABLE", "offers_source")
    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return jsonify({"ok": False, "error": "rows must be a list"}), 400
    if not rows:
        return jsonify({"ok": True, "inserted": 0})
    sb = get_supabase()
    # upsert to source table (id is pk)
    resp = sb.table(table).upsert(rows).execute()
    inserted = len(rows)
    return jsonify({"ok": True, "inserted": inserted, "table": table})

# GET /api/sync/last-changes?limit=50
@sync_admin_bp.get("/last-changes")
def last_changes():
    limit = int(request.args.get("limit", "50"))
    sb = get_supabase()
    res = sb.table(os.getenv("SYNC_DELTAS_TABLE", "sync_deltas")) \
            .select("*") \
            .order("change_ts", desc=True) \
            .limit(limit) \
            .execute()
    return jsonify({"rows": res.data or []})
