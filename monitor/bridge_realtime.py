import os, time, logging
from datetime import datetime, timezone
from typing import Any, Dict
from dotenv import load_dotenv
from supabase import create_client, Client
from telegram_sender import send_alert

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
MIN_CONF = float(os.getenv("ALERT_MIN_CONFIDENCE", "0.0"))
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def _meets_threshold(row: Dict[str, Any]) -> bool:
    c = row.get("confidence")
    return c is None or float(c) >= MIN_CONF

def _mark_sent(alert_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    sb.table("alerts").update({"status": "sent", "sent_at": now}).eq("id", alert_id).execute()

def _mark_failed(alert_id: str, reason: str) -> None:
    sb.table("alerts").update({"status": "failed"}).eq("id", alert_id).execute()
    logging.error(f"Alert {alert_id} failed: {reason}")

def _handle_insert(new_row: Dict[str, Any]) -> None:
    alert_id = new_row.get("id")
    if new_row.get("status") != "pending":
        return
    if not _meets_threshold(new_row):
        logging.info(f"Skip alert {alert_id}: below threshold")
        return
    try:
        send_alert({
            "title": new_row.get("title"),
            "body": new_row.get("body"),
            "severity": new_row.get("severity"),
            "confidence": new_row.get("confidence"),
            "source": new_row.get("source"),
            "link": new_row.get("link"),
        })
        _mark_sent(alert_id)
        logging.info(f"Sent alert {alert_id}")
    except Exception as e:
        _mark_failed(alert_id, str(e))

def run():
    ch = sb.channel("realtime:public:alerts")

    def on_insert(payload):
        try:
            new_row = payload.get("record") or payload.get("new") or {}
            _handle_insert(new_row)
        except Exception as e:
            logging.exception(f"insert handler error: {e}")

    def on_update(payload):
        try:
            new_row = payload.get("record") or payload.get("new") or {}
            old_row = payload.get("old") or {}
            if (old_row.get("status") == "pending") and (new_row.get("status") == "pending"):
                _handle_insert(new_row)
        except Exception as e:
            logging.exception(f"update handler error: {e}")

    ch.on("postgres_changes", {"event": "INSERT", "schema": "public", "table": "alerts"}, on_insert)
    ch.on("postgres_changes", {"event": "UPDATE", "schema": "public", "table": "alerts"}, on_update)
    ch.subscribe()
    logging.info("Realtime bridge subscribed on public.alerts")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Realtime bridge stopped")

if __name__ == "__main__":
    run()
