from flask import Blueprint, jsonify, request
from services.drift_service import fetch_confidence_series, smooth_and_drift, summarize_drift
from utils.supa_client import supabase

forecast_bp = Blueprint("forecast_bp", __name__)

@forecast_bp.route("/forecast/drift", methods=["GET"])
def get_drift_forecast():
    try:
        days = int(request.args.get("days", 30))
        alpha = float(request.args.get("alpha", 0.35))
        series = fetch_confidence_series(supabase, days)
        result = smooth_and_drift(series, alpha)
        result["summary"] = summarize_drift(result.get("drift", []))
        return jsonify({"ok": True, "data": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
