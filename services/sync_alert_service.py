# =========================================
# backend/services/sync_alert_service.py
# Stage 13.99 — Alert History + Retry + Webhook Mirror
# =========================================
import os
import time
import requests
from datetime import datetime, timezone
from typing import Optional, Tuple

from utils.supabase_client import get_supabase
from services.alert_mirror_service import mirror_to_all

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ALERT_THRESHOLD = int(os.getenv("SYNC_ALERT_THRESHOLD", "10"))
ENABLE_ALERTS = os.getenv("ENABLE_SYNC_ALERTS", "true").lower() in ("1", "true", "yes")

RETRY_MAX = int(os.getenv("SYNC_ALERT_RETRY_MAX", "3"))
RETRY_DELAY_MS = int(os.getenv("SYNC_ALERT_RETRY_DELAY_MS", "1500"))

ALERT_TABLE = "sync_alert_log"


def _token_hint(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    return token[-6:]


def _log_alert(status: str, message: str, error: Optional[str], retry_count: int, sent_at: Optional[str]):
    sb = get_supabase()
    payload = {
        "status": status,
        "message": message,
        "error": error,
        "retry_count": retry_count,
        "chat_id": CHAT_ID,
        "token_hint": _token_hint(TELEGRAM_TOKEN),
        "sent_at": sent_at,
    }
    sb.table(ALERT_TABLE).insert(payload).execute()


def _send_once(text: str) -> Tuple[bool, Optional[str]]:
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return False, "missing-telegram-credentials"
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        resp = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
        if resp.ok:
            return True, None
        return False, f"{resp.status_code}:{resp.text[:200]}"
    except Exception as e:
        return False, str(e)


def _mirror_payload(text: str):
    return {
        "channel": "telegram",
        "chat_id": CHAT_ID,
        "message": text,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def send_with_retry(text: str) -> bool:
    """Try to send a Telegram message with retry & log to Supabase; mirror on success."""
    attempts = 0
    last_err = None
    while attempts <= RETRY_MAX:
        ok, err = _send_once(text)
        attempts += 1
        if ok:
            sent_ts = datetime.now(timezone.utc).isoformat()
            _log_alert("ok", text, None, attempts - 1, sent_ts)
            # mirror after success (non-blocking semantics simulated)
            try:
                mirror_to_all(_mirror_payload(text))
            except Exception:
                pass
            print("📨 Telegram alert sent (attempt:", attempts, ")")
            return True
        last_err = err
        if attempts <= RETRY_MAX:
            time.sleep(RETRY_DELAY_MS / 1000.0)
    _log_alert("failed", text, last_err, attempts - 1, None)
    print("⚠️ Telegram send failed after retries:", last_err)
    return False


def send_telegram_message(text: str) -> bool:
    return send_with_retry(text)


def maybe_alert_sync_delta(changed: int, color: str):
    if not ENABLE_ALERTS:
        return
    if changed >= ALERT_THRESHOLD:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        txt = (
            "🚨 <b>BuckDuit Sync Alert</b>\n\n"
            f"<b>Changes:</b> {changed}\n"
            f"<b>Status:</b> {color.upper()}\n"
            f"<b>Time (UTC):</b> {ts}"
        )
        send_with_retry(txt)


def retry_failed_alerts(limit: int = 50) -> int:
    sb = get_supabase()
    res = sb.table(ALERT_TABLE).select("*").eq("status", "failed").order("created_at", desc=True).limit(limit).execute()
    rows = res.data or []
    success = 0
    for r in rows:
        msg = r.get("message") or "(empty)"
        if send_with_retry(msg):
            success += 1
    return success


def resend_by_log_id(log_id: str) -> bool:
    """Load a past row from sync_alert_log and re-dispatch it (also mirrors)."""
    sb = get_supabase()
    res = sb.table(ALERT_TABLE).select("*").eq("id", log_id).limit(1).execute()
    rows = res.data or []
    if not rows:
        return False
    msg = rows[0].get("message") or "(empty)"
    return send_with_retry(msg)
