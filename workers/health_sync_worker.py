"""
Health Sync Worker
------------------
This worker pings the backend /api/system/status endpoint at intervals,
then updates the system_health table in Supabase for monitoring dashboards.
"""

import os
import sys
import time
import requests
from datetime import datetime

# 🔧 Ensure imports work in both local and production environments
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.supa_client import supabase  # ✅ dynamic path fix


def get_env(key: str, default=None):
    """Helper for environment variables."""
    return os.getenv(key, default)


def log(msg: str):
    """Simple timestamped logger."""
    print(f"[HealthSync] {datetime.utcnow().isoformat()} | {msg}")


def get_backend_status(base_url: str, path: str):
    """Fetch /api/system/status from backend."""
    try:
        url = f"{base_url.rstrip('/')}{path}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            log(f"⚠️ HTTP {res.status_code} on {url}")
            return None
    except Exception as e:
        log(f"❌ Error fetching {path}: {e}")
        return None


def upsert_health_status(data: dict):
    """Upsert backend health into Supabase table."""
    try:
        table = get_env("HEALTH_TABLE", "system_health")
        row_id = get_env("HEALTH_ROW_ID", "primary")

        payload = {
            "id": row_id,
            "backend": bool(data.get("backend")),
            "supabase": bool(data.get("supabase")),
            "ai_core": data.get("ai_core", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "raw": data,
        }

        supabase.table(table).upsert(payload).execute()
        log(f"✅ Upserted health: backend={payload['backend']} supabase={payload['supabase']} ai={payload['ai_core']}")
    except Exception as e:
        log(f"❌ Supabase upsert failed: {e}")


def main():
    """Main loop: check backend health and sync to Supabase."""
    backend_url = get_env("BACKEND_URL", "http://127.0.0.1:5000")
    health_path = get_env("HEALTH_PATH", "/api/system/status")
    interval = int(get_env("HEALTH_SYNC_INTERVAL", "60"))

    log(f"Starting worker | backend={backend_url} path={health_path} interval={interval}s")

    while True:
        status = get_backend_status(backend_url, health_path)
        if status:
            upsert_health_status(status)
        else:
            log("⚠️ Failed to get valid health status.")
        time.sleep(interval)


if __name__ == "__main__":
    main()
