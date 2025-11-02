import os
import time
import requests
import threading
from datetime import datetime, timezone
from supabase import create_client, Client

# =====================================================
#  BuckDuit AI Core — Stage 13.34
#  Telemetry + Auto-Healing Monitor
# =====================================================

# ✅ Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ✅ Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("✅ Supabase client initialized successfully.")
print("🚀 BuckDuit AI Core starting...")

# =====================================================
#  Telegram Alert Function
# =====================================================
def send_telegram_alert(message: str):
    """Send alert to Telegram if AI Core fails or hangs."""
    try:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️ Telegram credentials missing, skipping alert.")
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, json=payload, timeout=10)
        print(f"📨 Telegram alert sent: {message}")
    except Exception as e:
        print(f"⚠️ Telegram alert failed: {e}")

# =====================================================
#  Heartbeat (Telemetry) System
# =====================================================
def send_heartbeat():
    """Send periodic heartbeat to Supabase to confirm AI Core is alive."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        supabase.table("ai_core_status").upsert({"id": 1, "last_heartbeat": now}).execute()
        print(f"💓 Heartbeat sent at {now}")
    except Exception as e:
        print(f"⚠️ Failed to send heartbeat: {e}")
        send_telegram_alert(f"⚠️ Heartbeat failed: {e}")

def start_telemetry_monitor():
    """Background loop that keeps sending heartbeat every minute."""
    while True:
        send_heartbeat()
        time.sleep(60)  # every 1 minute

# =====================================================
#  Example Worker Threads (Simulated AI Workers)
# =====================================================
def summary_worker():
    """Simulated summary worker logic."""
    while True:
        print("🧠 Running summary worker...")
        time.sleep(30)

def adaptive_monitor():
    """Simulated adaptive alerts worker."""
    while True:
        print("📊 Monitoring adaptive signals...")
        time.sleep(45)

# =====================================================
#  Startup Sequence
# =====================================================
def start_all_workers():
    """Start all concurrent background threads."""
    threads = [
        threading.Thread(target=summary_worker, daemon=True),
        threading.Thread(target=adaptive_monitor, daemon=True),
        threading.Thread(target=start_telemetry_monitor, daemon=True)
    ]
    for t in threads:
        t.start()
    print("🧩 All AI Core workers started successfully.")

# =====================================================
#  Main Runtime Loop
# =====================================================
if __name__ == "__main__":
    try:
        start_all_workers()
        print("🧠 BuckDuit AI Core worker running main loop...")
        while True:
            time.sleep(10)  # keep alive
    except KeyboardInterrupt:
        print("🛑 Manual stop detected.")
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        send_telegram_alert(f"❌ BuckDuit AI Core crashed: {e}")
        raise
