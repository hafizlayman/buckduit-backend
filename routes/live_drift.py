# backend/routes/live_drift.py
from flask import Blueprint, request, jsonify
from services.live_drift_service import generate_live_drift

livedrift_bp = Blueprint("livedrift_bp", __name__)

@livedrift_bp.get("/live-smooth")
def live_smooth():
    """
    Example:
      /api/predictive/live-smooth?minutes=180&step=5&alpha=0.35
    """
    try:
        minutes = int(request.args.get("minutes", 180))
        step = int(request.args.get("step", 5))
        alpha = float(request.args.get("alpha", 0.35))
        data = generate_live_drift(minutes=minutes, step=step, alpha=alpha)
        return jsonify({"ok": True, "alpha": alpha, "step": step, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
