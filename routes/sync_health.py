# ==========================================================
# Sync Health API — Stage 14.04
# ==========================================================
from flask import Blueprint, jsonify
from datetime import datetime

sync_health_bp = Blueprint("sync_health_bp", __name__)

@sync_health_bp.route("/health", methods=["GET"])
def sync_health():
    """Simple sync health status endpoint."""
    return jsonify({
        "ok": True,
        "color": "green",
        "checked_at": datetime.utcnow().isoformat(),
        "message": "Sync services running normally"
    })
