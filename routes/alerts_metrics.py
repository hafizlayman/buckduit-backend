# backend/routes/alerts_metrics.py
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1️⃣ Load environment variables
# -----------------------------------------------------------------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise Exception("Supabase environment variables are missing. Check your .env file.")

# -----------------------------------------------------------------------------
# 2️⃣ Initialize Supabase client
# -----------------------------------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# -----------------------------------------------------------------------------
# 3️⃣ Create Blueprint
# -----------------------------------------------------------------------------
bp = Blueprint("alerts_metrics", __name__)

# -----------------------------------------------------------------------------
# 4️⃣ Route: /api/alerts/metrics
# -----------------------------------------------------------------------------
@bp.route("/api/alerts/metrics", methods=["GET"])
def get_alert_metrics():
    """Return summary metrics for alert severities."""
    try:
        # Get alert count by severity in the past 24 hours
        since_time = datetime.utcnow() - timedelta(hours=24)
        response = (
            supabase.table("alerts")
            .select("severity")
            .gte("timestamp", since_time.isoformat())
            .execute()
        )

        data = response.data
        total = len(data)
        severity_counts = {"CRITICAL": 0, "ERROR": 0, "WARNING": 0, "INFO": 0}

        for row in data:
            sev = row.get("severity", "").upper()
            if sev in severity_counts:
                severity_counts[sev] += 1

        return jsonify({
            "total_alerts": total,
            "by_severity": severity_counts,
            "updated_at": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------------------------
# 5️⃣ Route: /api/alerts/metrics/test
# -----------------------------------------------------------------------------
@bp.route("/api/alerts/metrics/test", methods=["GET"])
def test_alert_metrics():
    """Simple test route for verification."""
    return jsonify({
        "message": "alerts_metrics blueprint working",
        "time": datetime.utcnow().isoformat()
    })
