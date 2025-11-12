# =========================================
# services/alert_service.py
# Stage 14.03 — Telegram + Mirror delivery + logging
# =========================================
import os, time, uuid, requests
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from utils.supabase_client import get_supabase

# ---- Env ----
TG_TOKEN   = os.getenv("TELEGRAM_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TG_ENABLED = os.getenv("ENABLE_TELEGRAM_ALERTS", "false").lower() in ("1","true","yes")

MIRROR_SECRET = os.getenv("MIRROR_SHARED_SECRET", "").strip()
MIRROR_ENABLED = os.getenv("ENABLE_ALERT_MIRROR", "true").lower() in ("1","true","yes")

ALERT_LOGS = os.getenv("ALERT_LOG_TABLE", "alert_logs")
MIRRORS_TBL = os.getenv("ALERT_MIRRORS_TABLE", "alert_mirrors")

# ---- Helpers ----
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _log_row(status: str, message: str, channel: str, error: Optional[str]=None, meta: Optional[dict]=None, retry_count: int=0) -> Optional[str]:
    sb = get_supabase()
    payload = {
        "id": str(uuid.uuid4()),
        "created_at": _now_iso(),
        "status": status,
        "message": message,
        "channel": channel,
        "error": error,
        "retry_count": retry_count,
        "meta": meta or {},
    }
    try:
        sb.table(ALERT_LOGS).insert(payload).execute()
        return payload["id"]
    except Exception:
        return None

def _post_telegram(message: str) -> bool:
    if not (TG_ENABLED and TG_TOKEN and TG_CHAT_ID):
        _log_row("failed", message, "telegram", "disabled_or_missing_env")
        return False
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        rsp = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message}, timeout=20)
        ok = 200 <= rsp.status_code < 300
        _log_row("sent" if ok else "failed", message, "telegram", None if ok else f"status={rsp.status_code}")
        return ok
    except Exception as e:
        _log_row("failed", message, "telegram", str(e))
        return False

def _post_mirrors(message: str) -> None:
    if not MIRROR_ENABLED:
        return
    sb = get_supabase()
    try:
        rows = sb.table(MIRRORS_TBL).select("*").eq("enabled", True).limit(100).execute().data or []
    except Exception:
        rows = []

    for m in rows:
        url = (m.get("url") or "").strip()
        if not url:
            continue
        ok, err = False, None
        try:
            headers = {}
            if MIRROR_SECRET:
                headers["X-Mirror-Secret"] = MIRROR_SECRET
            r = requests.post(url, json={"message": message, "ts": _now_iso()}, headers=headers, timeout=20)
            ok = 200 <= r.status_code < 300
            if not ok:
                err = f"status={r.status_code}"
        except Exception as e:
            err = str(e)

        # update mirror status
        try:
            get_supabase().table(MIRRORS_TBL).update({
                "last_status": "ok" if ok else "failed",
                "last_error": None if ok else err,
                "last_sent_at": _now_iso(),
            }).eq("id", m["id"]).execute()
        except Exception:
            pass

# ---- Public API used by routes ----
def get_alert_status() -> Dict[str, Any]:
    return {
        "enabled": TG_ENABLED,
        "chat_id": TG_CHAT_ID or None,
        "threshold": float(os.getenv("ALERT_DELTA_THRESHOLD", "10")),
        "mirrors_enabled": MIRROR_ENABLED,
    }

def list_alert_history(limit: int=25) -> List[Dict[str, Any]]:
    sb = get_supabase()
    try:
        res = sb.table(ALERT_LOGS).select("*").order("created_at", desc=True).limit(limit).execute()
        return res.data or []
    except Exception:
        return []

def resend_from_log(log_id: str) -> bool:
    if not log_id:
        return False
    sb = get_supabase()
    try:
        row = sb.table(ALERT_LOGS).select("*").eq("id", log_id).single().execute().data
        if not row:
            return False
        msg = row.get("message") or ""
        ok = _post_telegram(msg)
        _post_mirrors(msg)
        if ok:
            sb.table(ALERT_LOGS).update({"retry_count": (row.get("retry_count") or 0) + 1}).eq("id", log_id).execute()
        return ok
    except Exception:
        return False

def retry_failed_alerts(hours: int=24) -> int:
    sb = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    try:
        res = sb.table(ALERT_LOGS).select("*").gte("created_at", cutoff).eq("status", "failed").limit(500).execute()
        rows = res.data or []
    except Exception:
        rows = []
    count = 0
    for r in rows:
        if resend_from_log(r.get("id")):
            count += 1
    return count

# ---- Mirrors ----
def list_mirrors() -> List[Dict[str, Any]]:
    try:
        return get_supabase().table(MIRRORS_TBL).select("*").order("created_at", desc=True).limit(200).execute().data or []
    except Exception:
        return []

def add_mirror(url: str) -> Optional[str]:
    if not url:
        return None
    mid = str(uuid.uuid4())
    try:
        get_supabase().table(MIRRORS_TBL).insert({
            "id": mid,
            "url": url,
            "enabled": True,
            "created_at": _now_iso(),
        }).execute()
        return mid
    except Exception:
        return None

def toggle_mirror(mid: str, enabled: bool) -> bool:
    try:
        get_supabase().table(MIRRORS_TBL).update({"enabled": enabled}).eq("id", mid).execute()
        return True
    except Exception:
        return False

def delete_mirror(mid: str) -> bool:
    try:
        get_supabase().table(MIRRORS_TBL).delete().eq("id", mid).execute()
        return True
    except Exception:
        return False

# ---- Test ----
def send_test_alert(message: str) -> bool:
    ok = _post_telegram(message)
    _post_mirrors(message)
    return ok

# ---- Bridge used by sync service (thresholded) ----
def maybe_alert_sync_delta(changed: int, health_color: str) -> None:
    try:
        threshold = int(float(os.getenv("ALERT_DELTA_THRESHOLD", "10")))
    except Exception:
        threshold = 10
    if changed >= threshold or health_color in ("red",):
        msg = f"🔔 Sync activity: changed={changed}, health={health_color}"
        _post_telegram(msg)
        _post_mirrors(msg)
