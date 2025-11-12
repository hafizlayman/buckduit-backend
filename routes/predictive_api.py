import os
from flask import Blueprint, jsonify, request
from services.predictive_service import compute_predictive_summary, build_anomaly_heatmap
from utils.supa_client import supabase

predictive_bp = Blueprint("predictive", __name__)

@predictive_bp.route("/status", methods=["GET"])
def predictive_status():
    return jsonify({"message": "Predictive API route is online.", "endpoint": "/api/predictive/predict"}), 200

# --- NEW: risk summary ---
@predictive_bp.route("/summary", methods=["GET"])
def predictive_summary():
    try:
        lookback_days = int(os.getenv("RISK_BASELINE_DAYS", "7"))
        z_alert = float(os.getenv("RISK_ALERT_ZSCORE", "1.8"))
        min_points = int(os.getenv("RISK_MIN_POINTS", "12"))

        # pull last N days of ai_score from supabase (fallback to empty)
        # Adjust table/source to your actual telemetry table
        rows = []
        try:
            # Example: ai_signals table with columns: timestamp, ai_score
            since = (datetime.utcnow() - timedelta(days=lookback_days+1)).isoformat()
            res = supabase.table("ai_signals").select("timestamp,ai_score").gte("timestamp", since).order("timestamp").execute()
            rows = res.data or []
        except Exception:
            rows = []

        summary = compute_predictive_summary(rows, lookback_days, z_alert, min_points)
        return jsonify(summary), 200 if summary.get("ok") else 202
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# --- NEW: anomaly heatmap dataset ---
@predictive_bp.route("/anomaly-map", methods=["GET"])
def anomaly_map():
    try:
        days = int(os.getenv("ANOMALY_MAP_DAYS", "7"))

        rows = []
        try:
            since = (datetime.utcnow() - timedelta(days=days+1)).isoformat()
            res = supabase.table("ai_signals").select("timestamp,ai_score").gte("timestamp", since).order("timestamp").execute()
            rows = res.data or []
        except Exception:
            rows = []

        payload = build_anomaly_heatmap(rows, days=days)
        return jsonify(payload), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# backend/routes/predictive_api.py

from flask import Blueprint, jsonify, request
from services.predictive_service import run_predictive_analysis

predictive_bp = Blueprint("predictive", __name__)

@predictive_bp.route("/predict", methods=["POST"])
def predict():
    """
    Endpoint for running predictive analysis.
    Expects a JSON payload from frontend.
    """
    try:
        data = request.get_json()
        result = run_predictive_analysis(data)
        return jsonify({"status": "success", "result": result}), 200
    except Exception as e:
        print(f"[Predictive API] Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@predictive_bp.route("/status", methods=["GET"])
def status():
    """
    Simple health check for predictive API route.
    """
    return jsonify({
        "message": "Predictive API route is online.",
        "endpoint": "/api/predictive/predict"
    }), 200
