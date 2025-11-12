# ==========================================================
# Predictive Drift Heatmap — mock
# ==========================================================
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import random

driftheatmap_bp = Blueprint("driftheatmap_bp", __name__)

@driftheatmap_bp.route("/drift-heatmap", methods=["GET"])
def drift_heatmap():
    # 5 rows (hours) × 5 columns (categories)
    categories = ["Freelance", "Gigs", "Investing", "Microtasks", "Surveys"]
    now = datetime.utcnow().replace(second=0, microsecond=0)
    rows = []
    for h in range(5):
        stamp = (now - timedelta(hours=(4 - h))).strftime("%H:%M")
        values = [round(random.uniform(2, 20), 3) for _ in categories]
        rows.append({"hour": stamp, "values": values})
    return jsonify({"ok": True, "columns": categories, "rows": rows})
