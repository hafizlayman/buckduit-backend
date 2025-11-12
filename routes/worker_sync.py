# backend/routes/worker_sync.py
from __future__ import annotations
from flask import Blueprint, jsonify
from monitor.adaptive_sync import apply_to_runtime, current_params

worker_sync_bp = Blueprint("worker_sync_bp", __name__)

@worker_sync_bp.get("/worker-params")
def get_worker_params():
    try:
        return jsonify({"status": "ok", "params": current_params()})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@worker_sync_bp.post("/worker-sync")
def post_worker_sync():
    try:
        applied = apply_to_runtime(source="manual_push")
        return jsonify({"status": "ok", "applied": applied})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
