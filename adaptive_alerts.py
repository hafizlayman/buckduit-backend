import os
import time
import requests
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone

# =====================================================
# ✅ Load Environment Variables
# =====================================================
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Your personal chat ID

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================
# ✅ Fetch latest report from Supabase
# =====================================================
def get_latest_report():
    try:
        res = supabase.table("report_logs").select("*").order("created_at", desc=True).limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        print("⚠️ Error fetching latest report:", e)
    return None

# =====================================================
# ✅ Send Telegram message
# =====================================================
def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            print("✅ Telegram alert sent successfully.")
        else:
            print("⚠️ Failed to send Telegram alert:", r.text)
    except Exception as e:
        print("⚠️ Telegram send error:", e)

# =====================================================
# 🧩 Adaptive Alert Logic
# =====================================================
last_conf = None

def monitor_reports():
    global last_conf
    while True:
        latest = get_latest_report()
        if latest:
            avg_conf = latest.get("avg_confidence", 0)
            summary = latest.get("content", "")[:200]
            timestamp = latest.get("created_at", "N/A")

            if last_conf is None:
                last_conf = avg_conf
                print("🔹 Initial confidence recorded.")
            elif abs(avg_conf - last_conf) >= 0.1:
                trend = "📈 UP" if avg_conf > last_conf else "📉 DOWN"
                message = (
                    f"⚡ *AI Adaptive Alert — Confidence {trend}*\n"
                    f"*Prev:* {last_conf:.2f} → *Now:* {avg_conf:.2f}\n"
                    f"🕒 {timestamp}\n\n"
                    f"🧾 *Summary Preview:*\n{summary}..."
                )
                send_telegram_message(message)
                last_conf = avg_conf
        else:
            print("No new report found yet.")

        time.sleep(180)  # check every 3 minutes

# =====================================================
# 🚀 Run when executed
# =====================================================
if __name__ == "__main__":
    print("🚀 Starting AI Adaptive Alert Monitor...")
    monitor_reports()
