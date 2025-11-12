import os, datetime
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def log_event(event_type: str, status: str = "info", details: str = "", recovery_time: float = 0, confidence: float = 0, ai_signal: str = None):
    """Insert a system log entry into Supabase."""
    try:
        data = {
            "event_type": event_type,
            "status": status,
            "details": details,
            "recovery_time": recovery_time,
            "confidence": confidence,
            "ai_signal": ai_signal,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        supabase.table("system_logs").insert(data).execute()
        print(f"🪶 Logged event → {event_type} ({status})")
    except Exception as e:
        print(f"⚠️ Failed to log event: {e}")
