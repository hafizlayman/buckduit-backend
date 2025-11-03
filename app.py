import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from datetime import datetime, timezone
import requests

# -------------------------
# 🔧 Environment Setup
# -------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

app = Flask(__name__)
CORS(app)

# -------------------------
# 🧩 Core Utilities
# -------------------------

def send_telegram(msg: str):
    """Send Telegram alerts."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not set.")
        return
    try:
        requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            params={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")

# -------------------------
# 🌐 ROUTES
# -------------------------

@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "message": "BuckDuit Backend Active",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/health")
def health_check():
    """Health endpoint that reports live AI Core status."""
    try:
        data = supabase.table("ai_core_heartbeats").select("*").order("timestamp", desc=True).limit(1).execute()
        last_heartbeat = data.data[0]["timestamp"] if data.data else None
        now = datetime.now(timezone.utc)

        # Compute seconds since last heartbeat
        if last_heartbeat:
            last_dt = datetime.fromisoformat(last_heartbeat.replace("Z", "+00:00"))
            diff = (now - last_dt).total_seconds()
        else:
            diff = None

        status = "UP" if diff is not None and diff < 180 else "DOWN"

        return jsonify({
            "status": status,
            "service": "AI_CORE",
            "last_heartbeat": last_heartbeat,
            "seconds_since_last": diff,
            "checked_at": now.isoformat()
        }), 200

    except Exception as e:
        print(f"❌ Health check error: {e}")
        return jsonify({"status": "DOWN", "error": str(e)}), 500


@app.route("/alerts/test", methods=["GET"])
def test_alert():
    """Trigger test Telegram alert."""
    msg = f"🚀 Test Alert from BuckDuit Backend at {datetime.now(timezone.utc).isoformat()}"
    send_telegram(msg)
    return jsonify({"sent": msg})


@app.route("/api/alerts/summary-card", methods=["GET"])
def summary_card():
    """Example API endpoint for dashboard summary."""
    try:
        offers = supabase.table("offers").select("rating, category").limit(10).execute()
        data = offers.data if offers.data else []
        return jsonify({"items": data})
    except Exception as e:
        print(f"❌ Summary card error: {e}")
        return jsonify({"error": str(e)}), 500


# -------------------------
# 🚀 Run Server
# -------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting BuckDuit Backend on port {port}")
    app.run(host="0.0.0.0", port=port)
