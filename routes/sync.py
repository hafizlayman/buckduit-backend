from flask import Blueprint, jsonify
from utils.time_utils import utcnow

sync_bp = Blueprint("sync_bp", __name__)

@sync_bp.route("/sync/health", methods=["GET"])
def sync_health():
    # Placeholder logic — replace later with actual worker status
    return jsonify({
        "ok": True,
        "color": "green",
        "checked_at": utcnow().isoformat()
    })
