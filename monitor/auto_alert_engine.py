import os
import time
import datetime
import requests
from supabase import create_client, Client

# === Load environment variables ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

ALERT_FILE = "backend/data/last_alert.txt"


# === Helper: Send Telegram Message ===
def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials missing — skipping alert.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=5)
        print(f"📨 Telegram alert sent.")
    except Exception as e:
        print(f"⚠️ Telegram send failed: {e}")


# === Helper: Log Alert to Supabase ===
def log_alert(signal):
    data = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event_type": "AI_SIGNAL_ALERT",
        "status": "pushed",
        "details": f"{signal['sector']} {signal['trend']}/{signal['risk_level']} → {signal['note']}",
    }
    try:
        supabase.table("system_logs").insert(data).execute()
    except Exception as e:
        print(f"⚠️ Failed to log alert: {e}")


# === Core Alert Worker ===
def run_auto_alert_loop(interval=60):
    print("🚨 Auto-Alert Engine started…")
    last_alert_time = 0

    while True:
        try:
            # fetch latest AI signal
            response = (
                supabase.table("ai_signals")
                .select("*")
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )

            if not response.data:
                time.sleep(interval)
                continue

            signal = response.data[0]
            ts = signal.get("timestamp")
            risk = signal.get("risk_level", "unknown")
            trend = signal.get("trend", "")
            sector = signal.get("sector", "")
            note = signal.get("note", "")
            signal_id = str(signal.get("id"))

            # prevent duplicate alert (based on file)
            if os.path.exists(ALERT_FILE):
                with open(ALERT_FILE, "r") as f:
                    last_id = f.read().strip()
                    if last_id == signal_id:
                        time.sleep(interval)
                        continue

            # only alert if risk high or critical or trend falling
            if risk in ["high", "critical"] or trend in ["falling", "volatile"]:
                message = (
                    f"⚠️ *BuckDuit AI Alert*\n"
                    f"Sector: {sector}\n"
                    f"Trend: {trend}\n"
                    f"Risk: {risk.upper()}\n"
                    f"Note: {note}\n"
                    f"Time: {ts}"
                )
                send_telegram_message(message)
                log_alert(signal)

                # update last alert record
                with open(ALERT_FILE, "w") as f:
                    f.write(signal_id)

            time.sleep(interval)

        except Exception as e:
            print(f"⚠️ Alert loop error: {e}")
            time.sleep(interval)
