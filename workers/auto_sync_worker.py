# =========================================
# workers/auto_sync_worker.py — Stage 14.02
# Background loop calling SyncService.run_once()
# =========================================
import os
import threading
import time

from services.sync_service import SyncService
from utils.ai_logger import log_event

INTERVAL = int(os.getenv("SYNC_INTERVAL_SECONDS", "60"))
SCOPE    = os.getenv("SYNC_SCOPE", "default")

def worker_loop():
    log_event("INFO", "auto_sync_worker", "worker loop started", scope=SCOPE,
              meta={"interval": INTERVAL})
    svc = SyncService()
    while True:
        try:
            result = svc.run_once()
            log_event("INFO", "auto_sync_worker", "tick complete", scope=SCOPE, meta=result)
        except Exception as e:
            log_event("ERROR", "auto_sync_worker", f"tick error: {e}", scope=SCOPE)
        time.sleep(INTERVAL)

def start_autosync_daemon():
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()
    # Keep the console line you already print in app.py
