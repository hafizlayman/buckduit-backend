import os, time, datetime
from supabase import create_client
import requests

print("🚀 BuckDuit AI Core worker starting...")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
        )
    except Exception as e:
        print("❌ Telegram error:", e)

while True:
    try:
        now = datetime.datetime.utcnow().isoformat()
        print(f"[{now}] 🧠 Running AI summary check...")
        data = supabase.table("alerts").select("*").limit(1).execute()
        print(f"Fetched {len(data.data)} alerts.")
    except Exception as e:
        print("❌ Worker error:", e)
        send_telegram(f"AI Core worker error: {e}")
    time.sleep(1800)  # run every 30 min
