# backend/services/telegram_notify.py
import os, requests

BOT = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram(text: str) -> bool:
    if not BOT or not CHAT:
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT, "text": text, "parse_mode": "Markdown"})
        return r.ok
    except Exception:
        return False
