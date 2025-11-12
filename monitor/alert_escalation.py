import os, time, json
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

supa: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
WINDOW_MINUTES = 10          # look-back window
THRESHOLD_CRITICAL = 3       # min critical count to trigger escalation
COOLDOWN_MINUTES = 30        # prevent spam

STATE_FILE = "/data/escalation_state.json"

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram creds missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
        print(f"📨 Sent escalation: {msg[:80]}...")
    except Exception as e:
        print("❌ Telegram failed:", e)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_escalation": None}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def fetch_recent_critical():
    since = (datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)).isoformat()
    resp = supa.table("alerts").select("*").gte("created_at", since).eq("severity", "CRITICAL").execute()
    return resp.data or []

def main():
    print("🚨 Alert Escalation Engine running...")
    state = load_state()
    while True:
        try:
            crit = fetch_recent_critical()
            count = len(crit)
            print(f"🧮 Found {count} criticals in last {WINDOW_MINUTES} min")

            last_time = state.get("last_escalation")
            cooldown_expired = (
                not last_time
                or datetime.now(timezone.utc)
                - datetime.fromisoformat(last_time)
                > timedelta(minutes=COOLDOWN_MINUTES)
            )

            if count >= THRESHOLD_CRITICAL and cooldown_expired:
                summary = "\n".join(
                    [f"- {c['source']} @ {c['created_at']}: {c['message']}" for c in crit[-THRESHOLD_CRITICAL:]]
                )
                msg = (
                    f"🚨 *CRITICAL ESCALATION TRIGGERED!*\n"
                    f"{count} critical alerts in {WINDOW_MINUTES} min window.\n\n{summary}"
                )
                send_telegram(msg)
                state["last_escalation"] = datetime.now(timezone.utc).isoformat()
                save_state(state)

        except Exception as e:
            print("❌ Engine error:", e)

        time.sleep(60)

if __name__ == "__main__":
    main()
