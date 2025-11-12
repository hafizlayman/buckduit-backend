# ==========================================================
# routes/predictive_mock.py — Stage 14.08 (Mock Predictive Suite)
# ==========================================================
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta, timezone
import math
import random

# ✅ This is the missing blueprint definition
predictive_mock_bp = Blueprint("predictive_mock_bp", __name__)

# --------- Helper functions ---------
def _ts_minutes_ago(n):
    return (datetime.now(timezone.utc) - timedelta(minutes=n)).isoformat()

def _series(n=36, base_amp=0.12, noise=0.02):
    """Produce a smooth-ish wave with noise for mock charts."""
    data = []
    for i in range(n):
        angle = (i / max(1, n - 1)) * math.pi * 2
        true_val = base_amp * math.sin(angle) * 0.8
        pred_val = true_val * 0.85 + (random.random() - 0.5) * noise
        smooth = pred_val * 0.85
        bias = pred_val - true_val
        data.append({
            "time": _ts_minutes_ago((n - i) * 5),
            "actual_drift": round(true_val, 6),
            "predicted_drift": round(pred_val, 6),
            "smoothed_drift": round(smooth, 6),
            "bias": round(bias, 6),
        })
    return data


# --------- ROUTES ---------
@predictive_mock_bp.route("/drift-forecast")
def drift_forecast():
    days = int(request.args.get("days", 30))
    alpha = float(request.args.get("alpha", 0.35))
    data = _series(n=36)
    avg_acc = 98.6
    return jsonify({"ok": True, "days": days, "alpha": alpha, "avg_accuracy": avg_acc, "data": data})


@predictive_mock_bp.route("/drift-heatmap")
def drift_heatmap():
    grid = [[round((math.sin(r / 3) + math.cos(c / 4)) * 0.1 + (random.random() - 0.5) * 0.02, 6)
             for c in range(24)] for r in range(7)]
    return jsonify({"ok": True, "grid": grid})


@predictive_mock_bp.route("/drift-memory")
def drift_memory():
    spikes = [{"time": _ts_minutes_ago(i * 30),
               "value": round(random.uniform(-0.15, 0.15), 6)} for i in range(10)]
    return jsonify({"ok": True, "spikes": spikes})


@predictive_mock_bp.route("/recovery-curve")
def recovery_curve():
    xs = list(range(0, 100, 5))
    conf = [round(0.4 + 0.6 * (1 - math.exp(-x / 35)), 3) for x in xs]
    vol = [round(0.6 * math.exp(-x / 30), 3) for x in xs]
    return jsonify({"ok": True, "x": xs, "confidence": conf, "volatility": vol})


@predictive_mock_bp.route("/stability-index")
def stability_index():
    stability = round(random.uniform(55, 82), 2)
    anomaly_density = round(random.uniform(0.25, 0.55), 3)
    volatility = round(random.uniform(0.22, 0.42), 3)
    return jsonify({"ok": True, "stability": stability,
                    "anomaly_density": anomaly_density, "volatility": volatility})


@predictive_mock_bp.route("/drift-comparison")
def drift_comparison():
    baseline = _series(n=24, base_amp=0.10)
    candidate = _series(n=24, base_amp=0.12)
    return jsonify({"ok": True, "baseline": baseline, "candidate": candidate})


@predictive_mock_bp.route("/adaptive-trend")
def adaptive_trend():
    xs = list(range(36))
    trend = [round(0.02 * math.sin(i / 5.0) + 0.001 * i, 4) for i in xs]
    return jsonify({"ok": True, "trend": trend, "x": xs})


@predictive_mock_bp.route("/tuner-state")
def tuner_state():
    state = {
        "target_accuracy": 0.920,
        "max_bias": 0.150,
        "learning_rate": 0.050,
        "correction_weight": 0.50,
        "notes": ""
    }
    return jsonify({"ok": True, **state})


@predictive_mock_bp.route("/bias-check")
def bias_check():
    alpha = float(request.args.get("alpha", 0.35))
    threshold = float(request.args.get("threshold", 0.12))
    data = _series(n=36)
    bias_abs_max = max(abs(d["bias"]) for d in data)
    flagged = bias_abs_max > threshold
    reasons = ["within guardrails"] if not flagged else [
        f"bias_abs_max {bias_abs_max:.3f} > threshold {threshold:.3f}"]
    return jsonify({
        "ok": True, "alpha": alpha, "threshold": threshold,
        "count": len(data),
        "bias_mean": round(sum(d['bias'] for d in data) / len(data), 6),
        "bias_abs_max": round(bias_abs_max, 6),
        "flagged": flagged, "reasons": reasons
    })


@predictive_mock_bp.route("/live-smooth")
def live_smooth():
    alpha = float(request.args.get("alpha", 0.35))
    data = _series(n=36)
    return jsonify({"ok": True, "alpha": alpha, "step": 5, "data": data})
