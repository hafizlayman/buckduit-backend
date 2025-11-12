# ==========================================================
# Drift Comparison (actual vs predicted) — mock
# ==========================================================
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import random

driftcomparison_bp = Blueprint("driftcomparison_bp", __name__)

@driftcomparison_bp.route("/drift-comparison", methods=["GET"])
def drift_comparison():
    now = datetime.utcnow()
    pts = []
    for i in range(10):
        t = (now - timedelta(minutes=(9 - i) * 5)).isoformat()
        actual = round(random.uniform(-0.2, 0.1), 3)
        predicted = round(actual + random.uniform(-0.02, 0.02), 3)
        pts.append({"time": t, "actual": actual, "predicted": predicted})
    # quick accuracy proxy
    diffs = [abs(p["actual"] - p["predicted"]) for p in pts]
    acc = round(100 * (1 - min(0.05, sum(diffs)/len(diffs) + 0.0)), 2)
    return jsonify({"ok": True, "points": pts, "avg_accuracy": acc})
