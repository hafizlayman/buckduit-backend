# =========================================
# backend/services/alert_mirror_service.py
# Stage 13.99 — Mirror alerts to external webhooks
# =========================================
import os
import json
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

from utils.supabase_client import get_supabase

ENABLE_MIRROR = os.getenv("ENABLE_ALERT_MIRROR", "true").lower() in ("1", "true", "yes")
MIRROR_SECRET = os.getenv("MIRROR_SHARED_SECRET", "")

TABLE = "alert_mirrors"


def list_mirrors() -> List[Dict[str, Any]]:
    sb = get_supabase()
    res = sb.table(TABLE).select("*").order("created_at", desc=True).execute()
    return res.data or []


def add_mirror(url: str) -> Dict[str, Any]:
    sb = get_supabase()
    res = sb.table(TABLE).insert({"url": url, "enabled": True}).execute()
    return (res.data or [{}])[0]


def set_mirror_enabled(mid: str, enabled: bool) -> Dict[str, Any]:
    sb = get_supabase()
    res = sb.table(TABLE).update({"enabled": enabled}).eq("id", mid).execute()
    return (res.data or [{}])[0]


def delete_mirror(mid: str) -> bool:
    sb = get_supabase()
    sb.table(TABLE).delete().eq("id", mid).execute()
    return True


def _update_result(mid: str, ok: bool, err: str | None):
    sb = get_supabase()
    sb.table(TABLE).update({
        "last_sent_at": datetime.now(timezone.utc).isoformat(),
        "last_status": "ok" if ok else "failed",
        "last_error": None if ok else err
    }).eq("id", mid).execute()


def mirror_to_all(payload: Dict[str, Any]) -> Tuple[int, int]:
    """Send alert payload to all enabled mirrors. Returns (ok_count, total)."""
    if not ENABLE_MIRROR:
        return (0, 0)

    ok = 0
    mirrors = [m for m in list_mirrors() if m.get("enabled")]
    for m in mirrors:
        url = m.get("url")
        mid = m.get("id")
        try:
            headers = {"Content-Type": "application/json"}
            if MIRROR_SECRET:
                headers["X-BuckDuit-Secret"] = MIRROR_SECRET
            r = requests.post(url, data=json.dumps(payload), headers=headers, timeout=15)
            if r.ok:
                ok += 1
                _update_result(mid, True, None)
            else:
                _update_result(mid, False, f"{r.status_code}:{r.text[:180]}")
        except Exception as e:
            _update_result(mid, False, str(e))
    return (ok, len(mirrors))
