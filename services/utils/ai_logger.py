# ==========================================================
# BuckDuit — AI Logger Utility
# ==========================================================
import os
import datetime
import json

LOG_LEVELS = ["DEBUG", "INFO", "WARN", "ERROR"]

def log_event(level="INFO", source="system", message="", data=None):
    """
    Simple unified logger for BuckDuit backend and workers.
    Prints JSON-style logs (safe for Render/Railway consoles).
    """
    if level not in LOG_LEVELS:
        level = "INFO"
    
    timestamp = datetime.datetime.utcnow().isoformat()
    entry = {
        "timestamp": timestamp,
        "level": level,
        "source": source,
        "message": message,
    }
    if data:
        entry["data"] = data

    try:
        print(json.dumps(entry, ensure_ascii=False))
    except Exception:
        print(f"[{timestamp}] [{level}] [{source}] {message}")
