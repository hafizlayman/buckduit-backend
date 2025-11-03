import os, time, socket, requests
from datetime import datetime, timezone
from supabase import create_client, Client

# ---- Env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SERVICE_NAME = os.getenv("SERVICE_NAME", "BuckDuit_AI_Core")
ENVIRONMENT = os.getenv("ENVIRONMENT", "prod")
HOST_LABEL = os.getenv("HOST_LABEL", socket.gethostname())
ALERT_CRON_MINUTES = int(os.getenv("ALERT_CRON_MINUTES", "30"))
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def sb() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def tg_send(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured; skipping send.")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10
        )
        print("📨 TG:", text)
    except Exception as e:
        print("❌ Telegram error:", e)

def upsert_heartbeat():
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "service_name": SERVICE_NAME,
        "env": ENVIRONMENT,
        "last_seen": now,
        "current_status": "UP",
        "meta": {"host": HOST_LABEL}
    }
    # composite unique key is (service_name, env) per earlier schema/policy
    sb().table("ai_core_heartbeats").upsert(
        payload, on_conflict="service_name,env"
    ).execute()
    print(f"💓 beat {now}")

def check_backend_and_alert():
    if not PUBLIC_BASE_URL:
        return
    try:
        r = requests.get(f"{PUBLIC_BASE_URL}/health", timeout=10)
        if r.status_code == 200:
            print("✅ backend /health OK")
        else:
            tg_send(f"🚨 {SERVICE_NAME} ({ENVIRONMENT}) backend unhealthy: {r.status_code}")
    except Exception as e:
        print("❌ backend unreachable:", e)
        tg_send(f"🚨 {SERVICE_NAME} ({ENVIRONMENT}) backend unreachable")

if __name__ == "__main__":
    print("🧠 AI Core worker booting…")
    # quick sanity ping on startup
    upsert_heartbeat()
    check_backend_and_alert()
    # steady-state loop
    interval = max(60, ALERT_CRON_MINUTES * 60)  # at least 60s
    while True:
        try:
            upsert_heartbeat()
            check_backend_and_alert()
        except Exception as e:
            print("❌ loop error:", e)
        time.sleep(interval)
