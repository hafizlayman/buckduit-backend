# backend/routes/policy_analytics.py
from flask import Blueprint, jsonify
import numpy as np
from datetime import datetime, timedelta

policy_analytics_bp = Blueprint("policy_analytics_bp", __name__)

# --- Mock data generator (replace with Supabase data when ready)
def get_confidence_data(days=7):
    base = 0.8
    trend = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=(days - i - 1))).strftime("%Y-%m-%d")
        avg_conf = base + 0.01 * i
        stability = round(0.75 + 0.02 * i, 2)
        trend.append({
            "date": date,
            "avg_confidence": avg_conf,
            "stability_index": stability
        })

    avg_conf = np.mean([t["avg_confidence"] for t in trend])
    avg_stability = np.mean([t["stability_index"] for t in trend])

    return {
        "status": "success",
        "metrics": {
            "avg_confidence": avg_conf,
            "avg_stability": avg_stability,
            "records": days
        },
        "trend": trend
    }

# --- Drift calculation
def get_drift_status():
    data = get_confidence_data(days=7)
    values = [t["avg_confidence"] for t in data["trend"]]
    today = values[-1]
    mean = np.mean(values)
    ema = np.mean(values[-3:])
    zscore = (today - mean) / np.std(values)
    delta_pct = ((today - mean) / mean) * 100
    return {
        "status": "ok",
        "today": today,
        "ema": ema,
        "mean": mean,
        "delta_pct": delta_pct,
        "zscore": zscore,
        "records": len(values)
    }

# --- Core endpoints
@policy_analytics_bp.route("/confidence_trend", methods=["GET"])
def confidence_trend():
    try:
        return jsonify(get_confidence_data()), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@policy_analytics_bp.route("/drift/status", methods=["GET"])
def drift_status():
    try:
        return jsonify(get_drift_status()), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# --- Prefixed routes for frontend consistency
@policy_analytics_bp.route("/api/policy/analytics/confidence_trend", methods=["GET"])
def prefixed_confidence_trend():
    return confidence_trend()


@policy_analytics_bp.route("/api/policy/analytics/drift/status", methods=["GET"])
def prefixed_drift_status():
    return drift_status()
