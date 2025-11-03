import os
import time
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# ──────────────────────────────────────────────
# 1️⃣ Load environment variables
# ──────────────────────────────────────────────
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
AI_CORE_HEALTH_URL = os.getenv("AI_CORE_HEALTH_URL")

# Validate required vars
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment variables.")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ──────────────────────────────────────────────
# 2️⃣ Telegram alert function
# ──────────────────────────────────────────────
def send_telegram_alert(message: str):
    """Send an alert message to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram config missing — skipping alert.")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ Telegram send failed: {e}")

# ──────────────────────────────────────────────
# 3️⃣ Health check loop
# ──────────────────────────────────────────────
FAIL_THRESHOLD = 3         # number of failed checks before alert
CHECK_INTERVAL = 30        # seconds between each check
failure_count = 0

print("🩺 Auto-Restart Monitor started...")
print(f"🔗 Watching {AI_CORE_HEALTH_URL}")

while True:
    try:
        response = requests.get(AI_CORE_HEALTH_URL, timeout=10)
        if response.status_code == 200:
            if failure_count > 0:
                print("✅ Service recovered — AI Core healthy again.")
                send_telegram_alert("✅ BuckDuit AI Core is healthy again.")
            failure_count = 0
        else:
            failure_count += 1
            print(f"⚠️ {time.strftime('%H:%M:%S')} — Health check failed ({failure_count})")

    except Exception as e:
        failure_count += 1
        print(f"⚠️ {time.strftime('%H:%M:%S')} — Health check failed ({failure_count}): {e}")

    # Trigger alert if threshold exceeded
    if failure_count >= FAIL_THRESHOLD:
        send_telegram_alert(f"🚨 BuckDuit AI Core is DOWN after {failure_count} checks!")
        failure_count = 0  # reset counter to avoid spamming

    time.sleep(CHECK_INTERVAL)
