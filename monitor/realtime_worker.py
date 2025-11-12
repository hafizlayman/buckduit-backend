import os
import time
import requests
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def send_telegram(msg: str):
    """Send message to Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not set — skipping.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, json=payload, timeout=10)
        print(f"📨 Telegram alert sent: {msg[:60]}...")
    except Exception as e:
        print("❌ Telegram send failed:", e)

def main():
    print("🚀 Realtime worker active...")

    def handle_alert(payload):
        new = payload["new"]
        msg = (
            f"🚨 *{new.get('severity','UNKNOWN')} ALERT*\n"
            f"Source: {new.get('source')}\n"
            f"Message: {new.get('message')}\n"
            f"Time: {new.get('created_at')}"
        )
        print(f"⚡ New alert: {msg}")
        send_telegram(msg)

    try:
        channel = (
            supabase.channel("realtime-alerts")
            .on(
                "postgres_changes",
                {"event": "INSERT", "schema": "public", "table": "alerts"},
                handle_alert,
            )
            .subscribe()
        )

        while True:
            time.sleep(10)

    except Exception as e:
        print("❌ Worker crashed:", e)
        time.sleep(5)
        main()  # auto-restart

if __name__ == "__main__":
    main()
