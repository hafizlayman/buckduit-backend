# ==========================================================
# Predictive Drift Memory — mock
# ==========================================================
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import random

driftmemory_bp = Blueprint("driftmemory_bp", __name__)

@driftmemory_bp.route("/drift-memory", methods=["GET"])
def drift_memory():
    # 10 points of historical drift "memory"
    now = datetime.utcnow()
    series = []
    for i in range(10):
        t = (now - timedelta(minutes=(9 - i) * 5)).isoformat()
        val = round(random.uniform(-0.25, 0.25), 3)
        series.append({"time": t, "drift": val})
    return jsonify({"ok": True, "series": series})
