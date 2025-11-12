# ==========================================================
# BuckDuit Heartbeat AI — Stable Railway Edition
# ==========================================================
import os, time, requests
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
HEALTH_URL = os.getenv("HEALTH_URL", "http://127.0.0.1:5000/health")
INTERVAL = int(os.getenv("WATCHDOG_INTERVAL_SECONDS", "60"))
FAIL_LIMIT = int(os.getenv("WATCHDOG_FAIL_THRESHOLD", "3"))
SERVICE_NAME = os.getenv("SERVICE_NAME", "buckduit-backend")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Heartbeat linked to Supabase")
    except Exception as e:
        print("⚠️ Failed to link Supabase:", e)

def log_event(msg, level="info"):
    print(f"[{level.upper()}] {msg}")
    if supabase:
        try:
            supabase.table("system_logs").insert({
                "severity": level,
                "message": msg,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }).execute()
        except Exception:
            pass

def check():
    try:
        r = requests.get(HEALTH_URL, timeout=5)
        return r.status_code == 200
    except:
        return False

def main():
    fails = 0
    while True:
        if check():
            print("💚 Heartbeat OK")
            fails = 0
        else:
            fails += 1
            log_event(f"❤️‍🔥 Health check failed ({fails}/{FAIL_LIMIT})", "warn")
            if fails >= FAIL_LIMIT:
                log_event(f"💀 {SERVICE_NAME} failed {FAIL_LIMIT}x — recovery triggered", "critical")
                fails = 0
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
