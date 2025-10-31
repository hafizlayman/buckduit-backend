from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import datetime
import requests

# ==============================================================
#  Load environment variables
# ==============================================================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
ALERT_CRON_MINUTES = int(os.getenv("ALERT_CRON_MINUTES", 5))

# ==============================================================
#  Initialize Flask + Supabase
# ==============================================================
app = Flask(__name__)
CORS(app)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
print("✅ Supabase connection successful.")

# ==============================================================
#  Telegram Utility
# ==============================================================
def send_telegram_message(text):
    """Send message to Telegram bot."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Telegram message sent successfully.")
        else:
            print(f"⚠️ Telegram send error: {response.text}")
    except Exception as e:
        print(f"❌ Telegram send failed: {e}")

# ==============================================================
#  Route: AI Summary Card
# ==============================================================
@app.route("/api/alerts/summary-card", methods=["GET"])
def summary_card():
    """Fetch data from Supabase offers → send summary to Telegram."""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = supabase.table("offers").select("*").execute()
        alerts = data.data or []

        # Format message
        msg = f"📊 <b>BuckDuit AI Summary Report</b> – {now}\n"
        msg += "------------------------------------\n"

        # Confidence zones
        low, mid, high = [], [], []
        for a in alerts:
            name = a.get("name", "N/A")
            conf = float(a.get("ai_confidence", 0))
            if conf < 0.5:
                low.append(f"{name} — {conf:.2f}")
            elif conf < 0.7:
                mid.append(f"{name} — {conf:.2f}")
            else:
                high.append(f"{name} — {conf:.2f}")

        msg += "\n❄️ Low (< 0.5):\n" + "\n".join(low or ["–"]) + "\n"
        msg += "\n⚡ Medium (0.5–0.7):\n" + "\n".join(mid or ["–"]) + "\n"
        msg += "\n🔥 High (> 0.7):\n" + "\n".join(high or ["–"]) + "\n"

        msg += "\nOverall Heatmap:\n🟩🟨🟥"
        msg += f"\nNext update = {ALERT_CRON_MINUTES} minutes."
        msg += "\n------------------------------------"

        send_telegram_message(msg)
        print(f"✅ Summary message sent successfully ({len(alerts)} records).")
        return jsonify({"status": "ok", "count": len(alerts)}), 200

    except Exception as e:
        print(f"❌ Summary broadcast failed: {e}")
        return jsonify({"error": str(e)}), 500

# ==============================================================
#  Route: Adaptive Feedback
# ==============================================================
from adaptive_logic import apply_feedback_learning

@app.route("/api/feedback/<app_name>/<sentiment>", methods=["GET"])
def feedback(app_name, sentiment):
    """Receives feedback and adjusts AI confidence for the app."""
    try:
        result = apply_feedback_learning(supabase, app_name, sentiment)
        send_telegram_message(f"🧠 BuckDuit AI Feedback Processed:\n{result}")
        print(f"✅ Feedback applied: {result}")
        return jsonify({"message": result}), 200
    except Exception as e:
        print(f"❌ feedback error: {e}")
        return jsonify({"error": str(e)}), 500

# ==============================================================
#  Scheduler Job (Auto summary every N minutes)
# ==============================================================
scheduler = BackgroundScheduler()

def scheduled_summary_job():
    """Auto-run summary broadcast via Telegram."""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🕒 [Scheduler] Running AI summary broadcast at {now}")
        response = requests.get("http://127.0.0.1:5000/api/alerts/summary-card", timeout=10)
        if response.status_code == 200:
            print(f"✅ Summary triggered successfully at {now}")
        else:
            print(f"⚠️ Summary route returned {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Scheduler error: {e}")

scheduler.add_job(scheduled_summary_job, "interval", minutes=ALERT_CRON_MINUTES)
scheduler.start()
print(f"🟢 Scheduler active: every {ALERT_CRON_MINUTES} minute(s)")

# ==============================================================
#  Run Flask
# ==============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
