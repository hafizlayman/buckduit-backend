import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = os.getenv("PUBLIC_BASE_URL") or "http://127.0.0.1:5000"  # fallback for local run

POLLING_INTERVAL = 3  # seconds


def send_message(text):
    """Send a message to Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ Telegram send error: {e}")


def process_feedback_command(command_text):
    """Parses and executes a /feedback command."""
    try:
        parts = command_text.strip().split()
        if len(parts) < 3:
            return "⚠️ Invalid feedback format. Use: /feedback <AppName> <good|bad>"

        _, app_name, sentiment = parts[:3]
        url = f"{BASE_URL}/api/feedback/{app_name}/{sentiment}"

        print(f"🔗 Sending feedback request to: {url}")

        # Try up to 3 times to avoid 503 temporary errors
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    return f"🧠 BuckDuit AI Feedback Processed:\n{data.get('message', 'No response')}"
                elif r.status_code >= 500:
                    print(f"⚠️ Attempt {attempt + 1}: Backend busy ({r.status_code}) — retrying...")
                    time.sleep(2)
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1}: Request error → {e}")
                time.sleep(2)

        return f"⚠️ Feedback request failed ({r.status_code}) – backend not responding"

    except Exception as e:
        return f"❌ Error processing feedback: {str(e)}"


def run_bot_polling():
    """Polls Telegram for new messages and processes feedback commands."""
    print("🤖 BuckDuit Telegram bot is running...")
    last_update_id = None

    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"offset": last_update_id, "timeout": 10}
            response = requests.get(url, params=params, timeout=15)
            data = response.json()

            if "result" in data:
                for update in data["result"]:
                    last_update_id = update["update_id"] + 1
                    message = update.get("message", {})
                    text = message.get("text", "")
                    chat_id = message.get("chat", {}).get("id")

                    if chat_id == int(CHAT_ID) and text.startswith("/feedback"):
                        print(f"📩 Command received: {text}")
                        reply = process_feedback_command(text)
                        send_message(reply)

            time.sleep(POLLING_INTERVAL)

        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_bot_polling()
