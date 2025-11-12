# backend/monitor/alert_watcher.py
import json, os, time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from supabase import Client
from monitor.supa_client import get_supabase
from monitor.telegram_sender import send_telegram_message

load_dotenv()

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "alert_push_state.json")
STATE_PATH = os.path.abspath(STATE_PATH)

SEV_RANK = {"INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_state() -> Dict[str, Any]:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_seen_ts": None, "last_seen_id": None}

def save_state(state: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def env_bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")

def min_severity_rank() -> int:
    lvl = os.getenv("ALERT_PUSH_MIN_SEVERITY", "ERROR").strip().upper()
    return SEV_RANK.get(lvl, 3)

def poll_seconds() -> int:
    try:
        return int(os.getenv("ALERT_PUSH_POLL_SECONDS", "8"))
    except Exception:
        return 8

def lookback_hours() -> int:
    try:
        return int(os.getenv("ALERT_PUSH_WINDOW_HOURS", "24"))
    except Exception:
        return 24

def format_alert_msg(row: Dict[str, Any]) -> str:
    ts = row.get("timestamp") or row.get("created_at") or now_utc_iso()
    sev = (row.get("severity") or "UNKNOWN").upper()
    src = row.get("ai_signal") or row.get("source") or "UNKNOWN"
    cat = row.get("event_type") or row.get("category") or "-"
    msg = row.get("details") or row.get("message") or "(no details)"
    meta = row.get("meta") or {}

    lines = [
        f"⚠️ *{sev}* · {src} · {cat}",
        f"🕒 {ts}",
        f"📝 {msg}",
    ]
    if isinstance(meta, dict) and meta:
        lines.append(f"🔧 meta: `{json.dumps(meta, ensure_ascii=False)}`")
    return "\n".join(lines)

def fetch_new_alerts(supa: Client, since_iso: str, limit: int = 100) -> List[Dict[str, Any]]:
    # Pull from the underlying table because it is the canonical store
    q = supa.table("system_logs") \
            .select("*") \
            .gte("timestamp", since_iso) \
            .order("timestamp", desc=False) \
            .limit(limit)
    data = q.execute().data or []
    return data

def run_loop() -> None:
    if not env_bool("ALERT_PUSH_ENABLED", True):
        print("Alert watcher disabled via ALERT_PUSH_ENABLED=false")
        return

    min_rank = min_severity_rank()
    supa = get_supabase()
    state = load_state()

    # initial since time
    since_ts = state.get("last_seen_ts")
    if not since_ts:
        since_ts = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours())).isoformat()

    print(f"[watcher] starting. min_severity_rank={min_rank}, since={since_ts}")
    save_every = 0

    while True:
        try:
            rows = fetch_new_alerts(supa, since_ts, limit=200)
            pushed = 0
            for row in rows:
                sev = (row.get("severity") or "INFO").upper()
                if SEV_RANK.get(sev, 1) < min_rank:
                    continue

                # push to Telegram
                text = format_alert_msg(row)
                try:
                    send_telegram_message(text, parse_mode="Markdown")
                    pushed += 1
                except Exception as te:
                    print(f"[watcher] telegram send failed: {te}")

                # update state cursor
                since_ts = row.get("timestamp") or row.get("created_at") or since_ts
                state["last_seen_ts"] = since_ts
                state["last_seen_id"] = row.get("id")

            save_every += 1
            if pushed or save_every >= 10:
                save_state(state)
                save_every = 0

            time.sleep(poll_seconds())

        except KeyboardInterrupt:
            print("[watcher] keyboard interrupt — stopping")
            break
        except Exception as e:
            print(f"[watcher] loop error: {e}")
            time.sleep(max(3, poll_seconds()))
