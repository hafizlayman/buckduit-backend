# ==========================================================
# Predictive Recovery Curve — mock
# ==========================================================
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import random

recoverycurve_bp = Blueprint("recoverycurve_bp", __name__)

@recoverycurve_bp.route("/recovery-curve", methods=["GET"])
def recovery_curve():
    # Simulate recovery from a dip
    now = datetime.utcnow()
    base = random.uniform(-0.3, -0.05)
    series = []
    for i in range(12):
        t = (now - timedelta(minutes=(11 - i) * 5)).isoformat()
        # upward trend from base toward zero
        val = round(base + (i/11.0)*abs(base), 3)
        series.append({"time": t, "value": val})
    return jsonify({"ok": True, "series": series, "message": "Mock recovery"})
