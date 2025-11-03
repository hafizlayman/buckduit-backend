# ==============================================================
# 🩺 BuckDuit AI Core Health Endpoint
# --------------------------------------------------------------
# Purpose:
#   Allows Railway + Health Monitor to verify uptime and status.
#   Returns 200 OK when the service is healthy.
# ==============================================================

from flask import Flask, jsonify
import os
from supabase import create_client, Client
from datetime import datetime, timezone

# --------------------------------------------------------------
# ✅ Initialize Flask app
# --------------------------------------------------------------
app = Flask(__name__)

# --------------------------------------------------------------
# 🧠 Load environment variables (used for validation)
# --------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# --------------------------------------------------------------
# 🔗 Initialize Supabase client (optional — can be skipped if not needed)
# --------------------------------------------------------------
supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase client initialized successfully for /health route")
    except Exception as e:
        print(f"⚠️ Warning: Supabase init failed in /health route — {e}")

# --------------------------------------------------------------
# 🩺 HEALTH ENDPOINT
# --------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health_check():
    try:
        # Optional: write a quick heartbeat log into your Supabase table
        if supabase:
            supabase.table("ai_core_heartbeats").insert({
                "service_name": "AI_CORE",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }).execute()

        # Return healthy response
        return jsonify({
            "status": "UP",
            "service": "BuckDuit AI Core",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return jsonify({
            "status": "DOWN",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

# --------------------------------------------------------------
# 🏁 Root route (optional, helps check base connection)
# --------------------------------------------------------------
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "message": "🧠 BuckDuit AI Core Backend Running",
        "status": "OK",
        "time": datetime.now(timezone.utc).isoformat()
    }), 200

# --------------------------------------------------------------
# 🚀 Main entry point
# --------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting AI Core on port {port} ...")
    app.run(host="0.0.0.0", port=port)
