# ================================================================
# BuckDuit — Telegram Alert Relay (Stage 13.96)
# ================================================================
import os, requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(title: str, msg: str, color: str = "#ffffff"):
    """Send formatted alert to Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Missing Telegram credentials, skipping relay.")
        return False

    emoji = "⚠️" if "Risk" in title else "🧠"
    text = f"{emoji} *{title}*\n{msg}\n_Color code:_ `{color}`"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code == 200:
            print(f"✅ Telegram alert sent: {title}")
            return True
        else:
            print(f"❌ Telegram send failed: {r.text}")
            return False
    except Exception as e:
        print(f"⚠️ Telegram relay error: {e}")
        return False
