import os, time, requests, datetime
from supabase import create_client, Client

# 🔧 Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ALERT_CRON_MINUTES = int(os.getenv("ALERT_CRON_MINUTES", 30))

# ✅ Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
print("✅ Supabase client initialized successfully.")

def send_telegram(msg: str):
    """Send alert message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        print(f"📨 Telegram sent: {msg}")
    except Exception as e:
        print("❌ Telegram error:", e)

def send_heartbeat():
    """Insert new heartbeat row into Supabase"""
    ts = datetime.datetime.utcnow().isoformat()
    supabase.table("ai_core_heartbeats").insert({"timestamp": ts}).execute()
    print(f"💓 Heartbeat at {ts}")

def monitor_backend():
    """Ping backend /health route"""
    try:
        resp = requests.get(f"{PUBLIC_BASE_URL}/health", timeout=10)
        if resp.status_code == 200:
            print("✅ Backend alive")
        else:
            send_telegram("🚨 AI Core: Backend responded but not OK.")
    except Exception as e:
        print("❌ Backend down:", e)
        send_telegram("🚨 AI Core DOWN — backend unreachable.")

def run_forever():
    print("🧠 BuckDuit AI Core starting…")
    while True:
        send_heartbeat()
        monitor_backend()
        time.sleep(ALERT_CRON_MINUTES * 60)

if __name__ == "__main__":
    run_forever()
