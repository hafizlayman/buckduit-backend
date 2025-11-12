import os
import requests
from dotenv import load_dotenv

# ==================================================
# ✅ Load environment
# ==================================================
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise Exception("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")

# ==================================================
# 🚀 Function: send_telegram_message
# ==================================================
def send_telegram_message(message: str):
    """Send a formatted Telegram alert message."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        response = requests.post(url, data=payload)

        if response.status_code == 200:
            print(f"✅ Telegram sent: {message}")
        else:
            print(f"⚠️ Telegram failed [{response.status_code}]: {response.text}")

    except Exception as e:
        print(f"❌ Telegram error: {e}")
