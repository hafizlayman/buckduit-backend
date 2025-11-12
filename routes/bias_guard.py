# backend/routes/bias_guard.py
from flask import Blueprint, request, jsonify
from services.live_drift_service import generate_live_drift, summarize_bias

biasguard_bp = Blueprint("biasguard_bp", __name__)

@biasguard_bp.get("/bias-check")
def bias_check():
    """
    Example:
      /api/predictive/bias-check?minutes=180&alpha=0.35&threshold=0.12
    """
    try:
        minutes = int(request.args.get("minutes", 180))
        step = int(request.args.get("step", 5))
        alpha = float(request.args.get("alpha", 0.35))
        threshold = float(request.args.get("threshold", 0.12))

        series = generate_live_drift(minutes=minutes, step=step, alpha=alpha)
        summary = summarize_bias(series, threshold=threshold)
        summary["count"] = len(series)
        summary["alpha"] = alpha
        return jsonify(summary)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
