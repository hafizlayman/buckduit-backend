import os
import time
from flask import Flask, jsonify
from supabase import create_client, Client

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("⚠️ Missing Supabase environment variables!")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase client initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        supabase = None


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health endpoint used by Railway + monitor."""
    try:
        if supabase:
            supabase.table("ai_core_heartbeats").select("id").limit(1).execute()
        return jsonify({
            "status": "ok",
            "service": "BuckDuit AI Core",
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "🚀 BuckDuit AI Core service is running!",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
