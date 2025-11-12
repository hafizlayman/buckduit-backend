# backend/supervisor_daemon.py
# Stage 14.15 — umbrella supervisor that can start multiple background monitors

import os
from typing import List
from workers.drift_supervisor import start_background_thread as start_drift

START_DRIFT = (os.getenv("ENABLE_DRIFT_SUPERVISOR", "1") == "1")

_threads: List = []

def start_all():
    if START_DRIFT:
        _threads.append(start_drift())
    # Reserve for future: heartbeat/auto-heal/etc (already started in earlier stages via start.sh)

if __name__ == "__main__":
    start_all()
    # Keep process alive if invoked directly
    import time
    while True:
        time.sleep(3600)
