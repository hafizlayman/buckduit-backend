import os
import time
from flask import Flask, jsonify
from supabase import create_client, Client

# ----------------------------------------------------------------
# ✅ Initialize Flask
# ----------------------------------------------------------------
app = Flask(__name__)

# ----------------------------------------------------------------
# ✅ Load Supabase Configuration
# ----------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("⚠️  Missing Supabase environment variables!")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase client initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        supabase = None

# ----------------------------------------------------------------
# ✅ Health Check Endpoint
# ----------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health_check():
    """
    Simple health endpoint used by Railway + Health Monitor.
    """
    try:
        # Optional Supabase ping (lightweight check)
        if supabase:
            _ = supabase.table("ai_core_heartbeats").select("id").limit(1).execute()

        return jsonify({
            "status": "ok",
            "service": "BuckDuit AI Core",
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500

# ----------------------------------------------------------------
# ✅ Root Endpoint (for manual test)
# ----------------------------------------------------------------
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "message": "🚀 BuckDuit AI Core service is running!",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }), 200

# ----------------------------------------------------------------
# ✅ Background Worker Logic (optional placeholder)
# ----------------------------------------------------------------
def start_workers():
    """
    Placeholder for async/monitor threads.
    You can safely start adaptive monitors, summary workers, etc.
    """
    print("🧠 Background workers ready... (placeholder)")
    # Example:
    # threading.Thread(target=summary_worker_loop, daemon=True).start()
    # threading.Thread(target=adaptive_monitor_loop, daemon=True).start()

# ----------------------------------------------------------------
# ✅ Entrypoint
# ----------------------------------------------------------------
if __name__ == "__main__":
    start_workers()
    app.run(host="0.0.0.0", port=5000)
