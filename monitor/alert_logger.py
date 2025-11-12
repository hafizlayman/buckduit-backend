# backend/monitor/alert_logger.py
from typing import Dict
from datetime import datetime
from supabase import Client

def log_alert(supabase: Client, severity: str, category: str, title: str, message: str, meta: Dict=None):
    payload = {
        "severity": severity,
        "category": category,
        "source": "core",
        "title": title,
        "message": message,
        "meta": meta or {},
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("alerts").insert(payload).execute()
