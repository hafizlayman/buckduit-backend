"""
Health Incident Worker
----------------------
Monitors backend uptime and triggers Telegram alerts after repeated failures.
"""

import os
import sys
import time
import requests
from datetime import datetime

# ✅ Path fix for local + production
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.supa_client import supabase
from services.notifier import send_telegram_message


def log(msg: str):
    """Simple timestamped logger."""
    print(f"[IncidentWorker] {datetime.utcnow().isoformat()} | {msg}")


def get_env(key: str, default=None):
    """Get environment variable with fallback."""
    return os.getenv(key, default)


def get_backend_status(base_url: str, path: str):
    """Ping system status endpoint."""
    try:
        url = f"{base_url.rstrip('/')}{path}"
        res = requests.get(url, timeout=10)
        return res.status_code == 200
    except Exception as e:
        log(f"⚠️ Connection error: {e}")
        return False


def insert_incident(status: str, message: str):
    """Write incident record into Supabase."""
    try:
        data = {
            "status": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        supabase.table("system_incidents").insert(data).execute()
        log(f"🧾 Logged incident: {status} | {message}")
    except Exception as e:
        log(f"❌ Failed to insert incident: {e}")


def main():
    """Main incident monitor loop."""
    backend_url = get_env("BACKEND_URL", "http://127.0.0.1:5000")
    health_path = get_env("HEALTH_PATH", "/api/system/status")
    interval = int(get_env("HEALTH_CHECK_INTERVAL", "60"))
    failure_threshold = int(get_env("HEALTH_FAILURE_THRESHOLD", "3"))

    log(f"Started Health Incident Worker | backend={backend_url} | interval={interval}s")

    failure_count = 0
    alert_sent = False

    while True:
        is_up = get_backend_status(backend_url, health_path)

        if is_up:
            if alert_sent:
                msg = "✅ System has recovered and is now reachable again."
                send_telegram_message(msg)
                insert_incident("recovered", msg)
                log("System recovered.")
                alert_sent = False
            failure_count = 0
        else:
            failure_count += 1
            log(f"❌ Failure {failure_count}/{failure_threshold}")

            if failure_count >= failure_threshold and not alert_sent:
                msg = f"⚠️ BuckDuit backend unreachable for {failure_threshold} consecutive checks."
                send_telegram_message(msg)
                insert_incident("failure", msg)
                alert_sent = True

        time.sleep(interval)


if __name__ == "__main__":
    main()
