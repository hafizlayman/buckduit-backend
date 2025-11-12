import os, time, requests
from datetime import datetime, timezone
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SERVICE_NAME = os.getenv("SERVICE_NAME", "BuckDuit_AI_Core")
ENVIRONMENT = os.getenv("ENVIRONMENT", "prod")
HEARTBEAT_TTL = int(os.getenv("HEARTBEAT_TTL_SECONDS", "90"))
INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "30"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_DEFAULT_CHAT_ID = os.getenv("TELEGRAM_DEFAULT_CHAT_ID")
TELEGRAM_ADMIN_CHAT_IDS = [i.strip() for i in os.getenv("TELEGRAM_ADMIN_CHAT_IDS","").split(",") if i.strip()]

def supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase credentials missing.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def send_telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ Telegram bot token missing.")
        return
    targets = []
    if TELEGRAM_DEFAULT_CHAT_ID:
        targets.append(TELEGRAM_DEFAULT_CHAT_ID)
    targets.extend(TELEGRAM_ADMIN_CHAT_IDS)
    for chat_id in targets:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"},
                timeout=10
            )
        except Exception as e:
            print("Telegram error:", e)

def log_event(sb: Client, event: str, details: dict):
    sb.table("ai_core_alerts_log").insert({
        "service_name": SERVICE_NAME,
        "env": ENVIRONMENT,
        "event": event,
        "details": details
    }).execute()

def check_once():
    sb = supabase_client()
    r = sb.table("ai_core_heartbeats").select("*").eq("service_name", SERVICE_NAME).eq("env", ENVIRONMENT).single().execute()
    hb = r.data
    now = datetime.now(timezone.utc)
    if not hb:
        return
    last_seen = datetime.fromisoformat(hb["last_seen"].replace("Z","+00:00")) if isinstance(hb["last_seen"], str) else now
    gap = (now - last_seen).total_seconds()
    status = hb.get("current_status","UP")

    if gap > HEARTBEAT_TTL and status != "DOWN":
        msg = (f"🚨 <b>{SERVICE_NAME}</b> ({ENVIRONMENT}) is <b>DOWN</b>\n"
               f"Last seen: {last_seen.isoformat()}\nGap: {int(gap)}s")
        send_telegram(msg)
        log_event(sb, "DOWN", {"gap": gap, "last_seen": last_seen.isoformat()})
        sb.table("ai_core_heartbeats").update({
            "current_status": "DOWN",
            "last_alerted_at": now.isoformat()
        }).eq("service_name", SERVICE_NAME).eq("env", ENVIRONMENT).execute()

    elif gap <= HEARTBEAT_TTL and status == "DOWN":
        msg = (f"✅ <b>{SERVICE_NAME}</b> ({ENVIRONMENT}) RECOVERED\n"
               f"Heartbeat OK at {last_seen.isoformat()} (gap={int(gap)}s)")
        send_telegram(msg)
        log_event(sb, "RECOVERED", {"gap": gap, "last_seen": last_seen.isoformat()})
        sb.table("ai_core_heartbeats").update({
            "current_status": "UP",
            "last_alerted_at": now.isoformat()
        }).eq("service_name", SERVICE_NAME).eq("env", ENVIRONMENT).execute()

if __name__ == "__main__":
    print("🛡️ Watchdog monitor running...")
    while True:
        try:
            check_once()
        except Exception as e:
            print("❌ monitor error:", e)
        time.sleep(INTERVAL)
