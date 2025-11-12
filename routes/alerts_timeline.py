# backend/routes/alerts_timeline.py
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Load environment variables
# -----------------------------------------------------------------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise Exception("Supabase environment variables are missing. Check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
bp = Blueprint("alerts_timeline", __name__)

# -----------------------------------------------------------------------------
# Helper — pick available timestamp column
# -----------------------------------------------------------------------------
def detect_date_column():
    """Auto-detect which column to use for time-based sorting."""
    try:
        meta = supabase.table("alerts").select("*").limit(1).execute()
        if not meta.data:
            return "created_at"
        keys = meta.data[0].keys()
        for c in ["timestamp", "created_at", "updated_at"]:
            if c in keys:
                return c
    except Exception:
        pass
    return "created_at"  # default fallback


# -----------------------------------------------------------------------------
# Route: /api/alerts/timeline
# -----------------------------------------------------------------------------
@bp.route("/api/alerts/timeline", methods=["GET"])
def get_alerts_timeline():
    try:
        hours = int(request.args.get("hours", 24))
        limit = int(request.args.get("limit", 10))
        since_time = datetime.utcnow() - timedelta(hours=hours)

        date_col = detect_date_column()

        response = (
            supabase.table("alerts")
            .select("*")
            .gte(date_col, since_time.isoformat())
            .order(date_col, desc=True)
            .limit(limit)
            .execute()
        )

        data = response.data
        return jsonify({"items": data, "count": len(data), "column_used": date_col}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------------------------
# Quick test route
# -----------------------------------------------------------------------------
@bp.route("/api/alerts/timeline/test", methods=["GET"])
def test_timeline():
    return jsonify({
        "message": "alerts_timeline blueprint working",
        "time": datetime.utcnow().isoformat()
    }), 200
