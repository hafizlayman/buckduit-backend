# ==========================================================
# routes/predictive_real.py
# Stage 14.10 — Real-mode predictive endpoints
# ==========================================================
from flask import Blueprint, jsonify, request, current_app
import os
from utils.ai_logger import log_event
from services.data_fusion_service import get_live_series, get_bias_window

predictive_real_bp = Blueprint("predictive_real", __name__)

def _ema(values, alpha=0.35):
    if not values: return []
    out = [values[0]]
    for i in range(1, len(values)):
        out.append(alpha*values[i] + (1-alpha)*out[i-1])
    return out

@predictive_real_bp.route("/live-smooth")
def live_smooth_real():
    alpha = float(request.args.get("alpha", os.getenv("REAL_SMOOTH_ALPHA", "0.35")))
    minutes = int(request.args.get("minutes", os.getenv("REAL_WINDOW_MIN", "180")))
    supa = getattr(current_app, "supabase", None)

    series = get_live_series(supa, minutes) if supa else []
    actual = [x["actual_drift"] for x in series]
    pred   = [x["predicted_drift"] for x in series]
    bias   = [x["bias"] for x in series]

    sm = _ema(actual, alpha) if actual else []

    data = []
    for i, x in enumerate(series):
        data.append({
            "time": x["time"],
            "actual_drift": actual[i] if i < len(actual) else 0,
            "predicted_drift": pred[i] if i < len(pred) else 0,
            "smoothed_drift": sm[i] if i < len(sm) else 0,
            "bias": bias[i] if i < len(bias) else 0
        })

    return jsonify({"ok": True, "alpha": float(alpha), "step": 5, "data": data})

@predictive_real_bp.route("/bias-check")
def bias_check_real():
    alpha = float(request.args.get("alpha", os.getenv("REAL_SMOOTH_ALPHA", "0.35")))
    threshold = float(request.args.get("threshold", os.getenv("BIAS_THRESHOLD", "0.12")))
    supa = getattr(current_app, "supabase", None)

    b = get_bias_window(supa) if supa else {"bias_abs_max": 0, "bias_abs_mean": 0, "n": 0}
    flagged = (b["bias_abs_max"] > threshold)
    reasons = []
    if flagged:
        reasons.append(f"bias_abs_max {b['bias_abs_max']:.3f} > threshold {threshold:.3f}")
    else:
        reasons.append("within guardrails")

    return jsonify({
        "ok": True,
        "alpha": float(alpha),
        "threshold": float(threshold),
        "count": b.get("n", 0),
        "bias_abs_max": round(b.get("bias_abs_max", 0), 6),
        "bias_mean": round(b.get("bias_abs_mean", 0), 6),
        "flagged": flagged,
        "reasons": reasons
    })
