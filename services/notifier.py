# backend/services/notifier.py
import os, requests
from utils.ai_logger import log_event

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "").strip()

def notify_telegram(text: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
        ok = r.status_code == 200
        if not ok:
            log_event("WARN", "notify", f"telegram failed [{r.status_code}]: {r.text}")
        return ok
    except Exception as e:
        log_event("ERROR", "notify", f"telegram exception: {e}")
        return False
