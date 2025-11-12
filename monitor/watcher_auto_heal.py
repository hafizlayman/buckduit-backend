# backend/monitor/watcher_auto_heal.py
import os
import time
import threading
import requests

# === Dynamic, OS-safe path setup ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FLAG_PATH = os.path.join(DATA_DIR, "RECOVER_NOW.flag")

# === Configuration ===
HEALTH_URL = "http://127.0.0.1:5000/api/health/update"   # change to Render URL if remote
TELEGRAM_API = "https://api.telegram.org/bot"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message: str):
    """Send Telegram notification to alert recovery."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Missing Telegram credentials (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).")
        return
    url = f"{TELEGRAM_API}{TELEGRAM_TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={"chat_id": CHAT_ID, "text": message})
        if res.status_code == 200:
            print("📨 Telegram alert sent successfully.")
        else:
            print(f"⚠️ Telegram alert failed: {res.status_code}")
    except Exception as e:
        print(f"❌ Telegram send error: {e}")

def mark_backend_recovered():
    """Update backend health status."""
    try:
        res = requests.post(HEALTH_URL, json={"status": "recovered"})
        if res.status_code == 200:
            print("✅ Backend marked as recovered.")
        else:
            print(f"⚠️ Backend health update failed: {res.status_code}")
    except Exception as e:
        print(f"❌ Health update error: {e}")

def watcher_loop():
    """Continuously monitor for the recovery flag file."""
    print("👀 Auto-Healer Watcher started…")
    print(f"📂 Watching flag path: {FLAG_PATH}")
    while True:
        try:
            if os.path.exists(FLAG_PATH):
                print("🩹 Recovery flag detected.")
                send_telegram_message("🩹 Auto-Healer triggered. System recovered successfully.")
                mark_backend_recovered()
                os.remove(FLAG_PATH)
                print("🧹 Flag deleted after recovery.")
        except Exception as e:
            print(f"⚠️ Watcher loop error: {e}")
        time.sleep(5)

def start_auto_heal_watcher():
    """Spawn watcher as background thread."""
    thread = threading.Thread(target=watcher_loop, daemon=True)
    thread.start()
