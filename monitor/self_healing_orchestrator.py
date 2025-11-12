import os, time, json, requests
from datetime import datetime, timezone, timedelta
from supabase import create_client, Client

# === ENVIRONMENT ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Optional: for future Render API control
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_SERVICE_IDS = os.getenv("RENDER_SERVICE_IDS", "")  # comma-separated

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
STATE_FILE = "/data/selfheal_state.json"
COOLDOWN_MINUTES = 15
MAX_ATTEMPTS = 3


def send_telegram(msg):
    """Send message to Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Missing Telegram credentials.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("❌ Telegram failed:", e)


def fetch_latest_errors(limit=10):
    """Grab recent ERROR/CRITICAL logs from Supabase."""
    since = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    res = (
        supabase.table("system_logs")
        .select("*")
        .gte("timestamp", since)
        .in_("severity", ["ERROR", "CRITICAL"])
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def restart_service(service_id):
    """Simulated Render API restart (can be replaced with real API call)."""
    print(f"🔁 Restart triggered for service: {service_id}")
    if not RENDER_API_KEY:
        return "⚠️ Render API KEY missing – skipped"
    try:
        resp = requests.post(
            f"https://api.render.com/v1/services/{service_id}/restart",
            headers={"Authorization": f"Bearer {RENDER_API_KEY}"},
            timeout=20,
        )
        return f"✅ Restarted {service_id}: {resp.status_code}"
    except Exception as e:
        return f"❌ Restart failed: {e}"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def main():
    print("🧠 AI Self-Healing Orchestrator active…")
    state = load_state()
    while True:
        try:
            errors = fetch_latest_errors()
            services = RENDER_SERVICE_IDS.split(",") if RENDER_SERVICE_IDS else []
            now = datetime.now(timezone.utc)

            if not errors:
                print("✅ System healthy.")
                time.sleep(300)
                continue

            for err in errors:
                src = err.get("source", "unknown")
                key = f"{src}_last"
                last_action = state.get(key)
                can_restart = (
                    not last_action
                    or now - datetime.fromisoformat(last_action)
                    > timedelta(minutes=COOLDOWN_MINUTES)
                )

                if can_restart:
                    msg = f"🚨 *Self-Heal Triggered* for `{src}`\nReason: {err['details'][:80]}"
                    send_telegram(msg)
                    for sid in services:
                        feedback = restart_service(sid.strip())
                        print(feedback)
                        send_telegram(feedback)
                    state[key] = now.isoformat()
                    save_state(state)
                else:
                    print(f"⏳ Cooldown active for {src}")

        except Exception as e:
            print("❌ Orchestrator error:", e)
            send_telegram(f"❌ *Self-Heal Error:* {e}")

        time.sleep(300)  # every 5 min


if __name__ == "__main__":
    main()
