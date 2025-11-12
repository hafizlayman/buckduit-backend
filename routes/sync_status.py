# =========================================
# backend/routes/sync_status.py
# Stage 13.95 — Auto-Sync Worker Daemon + Status Indicator
# =========================================
from flask import Blueprint, jsonify
import os
from services.sync_service import SyncService

# Blueprint
sync_bp = Blueprint("sync_bp", __name__, url_prefix="/api/sync")

# -----------------------------------------
# GET  /api/sync/status
# -----------------------------------------
@sync_bp.get("/status")
def get_status():
    svc = SyncService()
    color = svc.health_color()
    return jsonify({
        "scope": os.getenv("SYNC_SCOPE", "default"),
        "color": color
    })

# -----------------------------------------
# POST /api/sync/run-once
# -----------------------------------------
@sync_bp.post("/run-once")
def run_once():
    svc = SyncService()
    result = svc.run_once()
    return jsonify(result)
