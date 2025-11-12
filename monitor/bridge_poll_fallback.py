import os, time, logging
from typing import Any, Dict, List
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from telegram_sender import send_alert

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
INTERVAL = int(os.getenv("BRIDGE_POLL_INTERVAL_SEC", "5"))
MIN_CONF = float(os.getenv("ALERT_MIN_CONFIDENCE", "0.0"))

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def fetch_pending(limit: int = 20) -> List[Dict[str, Any]]:
    r = sb.table("alerts").select("*").eq("status", "pending").order("created_at", desc=False).limit(limit).execute()
    return r.data or []

def mark_sent(alert_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    sb.table("alerts").update({"status": "sent", "sent_at": now}).eq("id", alert_id).execute()

def mark_failed(alert_id: str) -> None:
    sb.table("alerts").update({"status": "failed"}).eq("id", alert_id).execute()

def run():
    logging.info(f"Polling fallback worker every {INTERVAL}s")
    while True:
        try:
            for row in fetch_pending():
                c = row.get("confidence")
                if c is not None and float(c) < MIN_CONF:
                    continue
                try:
                    send_alert({
                        "title": row.get("title"),
                        "body": row.get("body"),
                        "severity": row.get("severity"),
                        "confidence": row.get("confidence"),
                        "source": row.get("source"),
                        "link": row.get("link"),
                    })
                    mark_sent(row["id"])
                except Exception as e:
                    logging.exception(f"send failed: {e}")
                    mark_failed(row["id"])
        except Exception as e:
            logging.exception(f"poll loop error: {e}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    run()
