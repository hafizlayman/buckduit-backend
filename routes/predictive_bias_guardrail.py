# ==========================================================
# predictive_bias_guardrail.py — Stage 14.07 Support API
# ==========================================================
from flask import Blueprint, jsonify, request
import random

biasguard_bp = Blueprint("biasguard_bp", __name__)

@biasguard_bp.route("/bias-check")
def bias_check():
    """Simulated bias guardrail endpoint for drift monitor."""
    try:
        threshold = float(request.args.get("threshold", 0.12))
        alpha = float(request.args.get("alpha", 0.35))
        vals = [random.uniform(-0.1, 0.1) for _ in range(50)]
        mean = sum(vals) / len(vals)
        absmax = max(abs(v) for v in vals)
        flagged = absmax > threshold
        return jsonify({
            "ok": True,
            "threshold": threshold,
            "alpha": alpha,
            "bias_mean": round(mean, 5),
            "bias_abs_max": round(absmax, 5),
            "flagged": flagged
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
