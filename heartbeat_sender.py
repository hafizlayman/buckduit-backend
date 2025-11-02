import os, time, socket
from datetime import datetime, timezone
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SERVICE_NAME = os.getenv("SERVICE_NAME", "BuckDuit_AI_Core")
ENVIRONMENT = os.getenv("ENVIRONMENT", "prod")
HOST_LABEL = os.getenv("HOST_LABEL", socket.gethostname())
INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "30"))

def supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase credentials missing.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def send_heartbeat():
    sb = supabase_client()
    now = datetime.now(timezone.utc).isoformat()
    meta = {"host": HOST_LABEL}
    sb.table("ai_core_heartbeats").upsert({
        "service_name": SERVICE_NAME,
        "env": ENVIRONMENT,
        "last_seen": now,
        "current_status": "UP",
        "meta": meta
    }, on_conflict="service_name,env").execute()

if __name__ == "__main__":
    print("💓 Heartbeat sender running...")
    while True:
        try:
            send_heartbeat()
            print(f"✅ beat {datetime.utcnow().isoformat()}Z")
        except Exception as e:
            print("❌ heartbeat error:", e)
        time.sleep(INTERVAL)
