# backend/services/alert_service.py
import os
import time
import json
from typing import Any, Dict, List, Optional
import requests

from utils.supabase_client import get_supabase
from utils.ai_logger import log_event

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
ALERTS_ENABLED = os.getenv("ALERTS_ENABLED", "true").lower() in ("1", "true", "yes")
ALERT_THRESHOLD = float(os.getenv("ALERT_DEFAULT_THRESHOLD", "0.5"))

def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

class AlertService:
    def __init__(self):
        self.sb = get_supabase()

    # -----------------------------
    # Status / Config
    # -----------------------------
    def status(self) -> Dict[str, Any]:
        return {
            "enabled": ALERTS_ENABLED,
            "threshold": ALERT_THRESHOLD,
            "chat_id": TELEGRAM_CHAT_ID or None,
            "transport": "telegram" if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID else "none",
            "ts": _now_iso(),
        }

    # -----------------------------
    # History
    # -----------------------------
    def history(self, limit: int = 25) -> Dict[str, Any]:
        try:
            res = (
                self.sb.table("alert_logs")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            rows = res.data or []
            return {"rows": rows}
        except Exception as e:
            log_event("ERROR", "alerts_history", f"fetch failed: {e}")
            return {"rows": [], "error": str(e)}

    # -----------------------------
    # Mirrors (Zapier/Discord/Webhooks)
    # -----------------------------
    def list_mirrors(self) -> Dict[str, Any]:
        try:
            res = self.sb.table("alert_mirrors").select("*").order("created_at", desc=True).execute()
            return {"rows": res.data or []}
        except Exception as e:
            log_event("ERROR", "alerts_mirrors", f"list failed: {e}")
            return {"rows": [], "error": str(e)}

    def add_mirror(self, url: str) -> Dict[str, Any]:
        try:
            row = {"url": url, "enabled": True}
            res = self.sb.table("alert_mirrors").insert(row).execute()
            return {"ok": True, "row": (res.data or [None])[0]}
        except Exception as e:
            log_event("ERROR", "alerts_mirrors", f"add failed: {e}", meta={"url": url})
            return {"ok": False, "error": str(e)}

    def update_mirror(self, mirror_id: str, enabled: bool) -> Dict[str, Any]:
        try:
            self.sb.table("alert_mirrors").update({"enabled": enabled}).eq("id", mirror_id).execute()
            return {"ok": True}
        except Exception as e:
            log_event("ERROR", "alerts_mirrors", f"update failed: {e}", meta={"id": mirror_id})
            return {"ok": False, "error": str(e)}

    def delete_mirror(self, mirror_id: str) -> Dict[str, Any]:
        try:
            self.sb.table("alert_mirrors").delete().eq("id", mirror_id).execute()
            return {"ok": True}
        except Exception as e:
            log_event("ERROR", "alerts_mirrors", f"delete failed: {e}", meta={"id": mirror_id})
            return {"ok": False, "error": str(e)}

    # -----------------------------
    # Retry / Resend
    # -----------------------------
    def retry_failed(self) -> Dict[str, Any]:
        """Re-send last 25 failed alerts to Telegram + mirrors."""
        try:
            failed = (
                self.sb.table("alert_logs")
                .select("*")
                .eq("status", "failed")
                .order("created_at", desc=True)
                .limit(25)
                .execute()
            ).data or []

            count = 0
            for row in failed:
                msg = row.get("message", "")
                meta = row.get("meta") or {}
                ok = self._send_all(msg, meta)
                new_status = "sent" if ok else "failed"
                self.sb.table("alert_logs").update(
                    {"status": new_status, "retry_count": (row.get("retry_count") or 0) + 1}
                ).eq("id", row["id"]).execute()
                count += 1 if ok else 0

            return {"resent": count}
        except Exception as e:
            log_event("ERROR", "alerts_retry", f"retry failed: {e}")
            return {"resent": 0, "error": str(e)}

    def resend_from_log(self, log_id: str) -> Dict[str, Any]:
        try:
            row = (
                self.sb.table("alert_logs")
                .select("*")
                .eq("id", log_id)
                .limit(1)
                .execute()
            ).data
            if not row:
                return {"ok": False, "error": "log not found"}
            row = row[0]
            ok = self._send_all(row.get("message",""), row.get("meta") or {})
            self.sb.table("alert_logs").update(
                {"status": "sent" if ok else "failed", "retry_count": (row.get("retry_count") or 0) + 1}
            ).eq("id", log_id).execute()
            return {"ok": ok}
        except Exception as e:
            log_event("ERROR", "alerts_resend", f"resend failed: {e}", meta={"id": log_id})
            return {"ok": False, "error": str(e)}

    # -----------------------------
    # Transport(s)
    # -----------------------------
    def _send_telegram(self, text: str) -> bool:
        if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
            return False
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
            r = requests.post(url, json=payload, timeout=15)
            return bool(r.ok)
        except Exception as e:
            log_event("ERROR", "telegram", f"send failed: {e}")
            return False

    def _send_mirrors(self, text: str, meta: Dict[str, Any]) -> None:
        try:
            rows = self.sb.table("alert_mirrors").select("*").eq("enabled", True).execute().data or []
            for m in rows:
                try:
                    r = requests.post(m["url"], json={"message": text, "meta": meta}, timeout=15)
                    status = "ok" if r.ok else f"fail {r.status_code}"
                    self.sb.table("alert_mirrors").update(
                        {"last_status": status, "last_error": None if r.ok else r.text, "last_sent_at": _now_iso()}
                    ).eq("id", m["id"]).execute()
                except Exception as e:
                    self.sb.table("alert_mirrors").update(
                        {"last_status": "error", "last_error": str(e), "last_sent_at": _now_iso()}
                    ).eq("id", m["id"]).execute()
        except Exception as e:
            log_event("ERROR", "alerts_mirrors", f"broadcast failed: {e}")

    def _log(self, status: str, message: str, meta: Dict[str, Any]) -> None:
        try:
            self.sb.table("alert_logs").insert({
                "status": status,
                "message": message,
                "meta": meta or {},
                "retry_count": 0
            }).execute()
        except Exception as e:
            log_event("ERROR", "alerts_log", f"insert failed: {e}")

    def _send_all(self, text: str, meta: Dict[str, Any]) -> bool:
        # primary: telegram
        ok = self._send_telegram(text) if ALERTS_ENABLED else False
        # mirrors are best-effort
        self._send_mirrors(text, meta)
        # record
        self._log("sent" if ok else "failed", text, meta)
        return ok

    # Public helper for routes
    def send_test(self, message: str) -> Dict[str, Any]:
        ok = self._send_all(message, {"type": "test"})
        return {"ok": ok}
