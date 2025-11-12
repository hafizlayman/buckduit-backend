# ==========================================================
# BuckDuit AI Logger Utility
# Safe JSON-based unified logging for backend + workers
# ==========================================================
import datetime
import json

LOG_LEVELS = ["DEBUG", "INFO", "WARN", "ERROR"]

def log_event(level="INFO", source="system", message="", data=None):
    """Simple JSON logger for Render, Railway, and local runs."""
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
