# =========================================
# backend/services/sync_service.py
# Stage 13.98 + 14.02 — Live Source Sync + Alert Bridge + Logging
# =========================================
import os
import time
import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from utils.supabase_client import get_supabase
from services.sync_alert_service import maybe_alert_sync_delta
from utils.ai_logger import log_event

# --- Config ---
SCOPE = os.getenv("SYNC_SCOPE", "default")
STATUS_TABLE = os.getenv("SYNC_STATUS_TABLE", "sync_status")
DELTAS_TABLE = os.getenv("SYNC_DELTAS_TABLE", "sync_deltas")

SOURCE_MODE  = os.getenv("SYNC_SOURCE_MODE", "mock")      # supabase | http | mock
SOURCE_TABLE = os.getenv("SYNC_SOURCE_TABLE", "offers_source")
SOURCE_URL   = os.getenv("SYNC_SOURCE_URL")

TARGET_TABLE = os.getenv("SYNC_TARGET_TABLE", "offers")

GREEN_S  = int(os.getenv("SYNC_HEALTH_GREEN", "120"))
YELLOW_S = int(os.getenv("SYNC_HEALTH_YELLOW", "300"))


class SyncService:
    """Full synchronization between source and target tables."""

    def __init__(self) -> None:
        self.sb = get_supabase()
        log_event("INFO", "sync_service", "initialized", scope=SCOPE)

    # ----------------------------------
    # Source Readers (supabase/http/mock)
    # ----------------------------------
    def fetch_source(self) -> List[Dict[str, Any]]:
        """Retrieve latest data from Supabase, HTTP, or mock fallback."""
        log_event("DEBUG", "sync_service", f"fetch_source mode={SOURCE_MODE}", scope=SCOPE)

        if SOURCE_MODE == "supabase":
            res = self.sb.table(SOURCE_TABLE).select("*").limit(50000).execute()
            data = res.data or []
            log_event("INFO", "sync_service", f"fetched {len(data)} rows from {SOURCE_TABLE}", scope=SCOPE)
            return data

        if SOURCE_MODE == "http" and SOURCE_URL:
            r = requests.get(SOURCE_URL, timeout=20)
            r.raise_for_status()
            if "application/json" in r.headers.get("content-type", ""):
                data = r.json()
                log_event("INFO", "sync_service", f"http source returned {len(data)} rows", scope=SCOPE)
                return data
            log_event("WARN", "sync_service", "http source non-json", scope=SCOPE)
            return []

        # mock fallback
        now = int(time.time())
        base_id = now // 60
        demo = [
            {"id": f"demo-{base_id}",   "name": "Demo Platform",  "rating": 4.2, "region": "MY"},
            {"id": f"demo-{base_id-1}", "name": "Older Platform", "rating": 3.9, "region": "US"},
        ]
        log_event("INFO", "sync_service", "using mock source", scope=SCOPE, meta={"rows": len(demo)})
        return demo

    def fetch_current(self) -> Dict[str, Dict[str, Any]]:
        res = self.sb.table(TARGET_TABLE).select("*").limit(100000).execute()
        items = res.data or []
        log_event("DEBUG", "sync_service", f"fetch_current {len(items)} rows", scope=SCOPE)
        return {str(row.get("id")): row for row in items if row.get("id") is not None}

    # ----------------------------------
    # Delta Computation
    # ----------------------------------
    def compute_deltas(
        self, source: List[Dict[str, Any]], current: Dict[str, Dict[str, Any]]
    ) -> Tuple[List[Dict], List[Dict], List[str]]:
        inserts: List[Dict] = []
        updates: List[Dict] = []
        deletes: List[str] = []

        src_map = {str(x.get("id")): x for x in source if x.get("id") is not None}

        for rid, src_row in src_map.items():
            cur = current.get(rid)
            if not cur:
                inserts.append(src_row)
            else:
                to_compare = {k: v for k, v in src_row.items()}
                cur_cmp = {k: v for k, v in cur.items() if k in to_compare}
                if to_compare != cur_cmp:
                    updates.append(src_row)

        for rid in current.keys():
            if rid not in src_map:
                deletes.append(rid)

        log_event("INFO", "sync_service", "computed deltas",
                  scope=SCOPE, meta={"inserts": len(inserts), "updates": len(updates), "deletes": len(deletes)})
        return inserts, updates, deletes

    # ----------------------------------
    # Apply Deltas + Log
    # ----------------------------------
    def apply_deltas(self, inserts, updates, deletes) -> int:
        count = 0
        now = datetime.now(timezone.utc).isoformat()

        if inserts:
            payload = [{**r, "updated_at": now} for r in inserts]
            self.sb.table(TARGET_TABLE).insert(payload).execute()
            count += len(inserts)
            self._log_deltas("insert", payload)

        if updates:
            payload = [{**r, "updated_at": now} for r in updates]
            self.sb.table(TARGET_TABLE).upsert(payload).execute()
            count += len(updates)
            self._log_deltas("update", payload)

        if deletes:
            for rid in deletes:
                self.sb.table(TARGET_TABLE).delete().eq("id", rid).execute()
            count += len(deletes)
            self._log_deltas("delete", [{"id": rid} for rid in deletes])

        log_event("INFO", "sync_service", f"applied {count} changes", scope=SCOPE)
        return count

    def _log_deltas(self, change_type: str, rows: List[Dict[str, Any]]):
        payloads = [{
            "scope": SCOPE,
            "table_name": TARGET_TABLE,
            "row_id": str(r.get("id")) if r.get("id") else None,
            "change_type": change_type,
            "payload": r,
        } for r in rows]
        if payloads:
            self.sb.table(DELTAS_TABLE).insert(payloads).execute()

    # ----------------------------------
    # Status + Health
    # ----------------------------------
    def set_status(self, status: str, delta_count: int = 0, errors: str | None = None):
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "scope": SCOPE,
            "last_run_at": now,
            "status": status,
            "delta_count": delta_count,
            "errors": errors,
            "updated_at": now,
        }
        if status == "ok":
            data["last_ok_at"] = now
        self.sb.table(STATUS_TABLE).upsert(data, on_conflict="scope").execute()

    def health_color(self) -> str:
        res = self.sb.table(STATUS_TABLE).select("last_ok_at").eq("scope", SCOPE).single().execute()
        last_ok = res.data.get("last_ok_at") if res.data else None
        if not last_ok:
            return "red"
        try:
            ts = datetime.fromisoformat(last_ok.replace("Z", "+00:00"))
        except Exception:
            return "yellow"
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        if age <= GREEN_S:
            return "green"
        if age <= YELLOW_S:
            return "yellow"
        return "red"

    # ----------------------------------
    # One full run
    # ----------------------------------
    def run_once(self) -> Dict[str, Any]:
        try:
            log_event("INFO", "sync_service", "run_once started", scope=SCOPE)
            source = self.fetch_source()
            current = self.fetch_current()
            inserts, updates, deletes = self.compute_deltas(source, current)
            changed = self.apply_deltas(inserts, updates, deletes)
            self.set_status("ok", delta_count=changed)

            # Telegram alert bridge
            maybe_alert_sync_delta(changed, self.health_color())

            result = {"ok": True, "changed": changed, "color": self.health_color()}
            log_event("INFO", "sync_service", "run_once complete", scope=SCOPE, meta=result)
            return result
        except Exception as e:
            self.set_status("error", delta_count=0, errors=str(e))
            log_event("ERROR", "sync_service", f"run_once failed: {e}", scope=SCOPE)
            return {"ok": False, "error": str(e), "color": self.health_color()}
