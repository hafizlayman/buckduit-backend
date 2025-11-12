import os, time, json, requests
from datetime import datetime, timezone, timedelta
from supabase import create_client, Client

# ============================================================
# 🧠 BuckDuit Adaptive Learning Healer (v2)
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_SERVICE_IDS = os.getenv("RENDER_SERVICE_IDS", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

MEMORY_FILE = "/data/selfheal_memory.json"
STATE_FILE = "/data/selfheal_state.json"

COOLDOWN_MINUTES = 20
FAILURE_LIMIT = 3  # avoid restarting a service more than this within 24h


def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Missing Telegram credentials.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("❌ Telegram failed:", e)


def fetch_recent_errors(minutes=30):
    since = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
    res = (
        supabase.table("system_logs")
        .select("*")
        .gte("timestamp", since)
        .in_("severity", ["ERROR", "CRITICAL"])
        .order("timestamp", desc=True)
        .limit(10)
        .execute()
    )
    return res.data or []


def restart_service(service_id):
    print(f"🔁 Restart requested for service: {service_id}")
    if not RENDER_API_KEY:
        return "⚠️ No Render API key — skipping"
    try:
        resp = requests.post(
            f"https://api.render.com/v1/services/{service_id}/restart",
            headers={"Authorization": f"Bearer {RENDER_API_KEY}"},
            timeout=20,
        )
        return f"✅ Restarted {service_id} ({resp.status_code})"
    except Exception as e:
        return f"❌ Restart failed for {service_id}: {e}"


def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def record_result(memory, src, success):
    now = datetime.now(timezone.utc).isoformat()
    if src not in memory:
        memory[src] = []
    memory[src].append({"time": now, "success": success})
    # keep only last 20 entries per service
    memory[src] = memory[src][-20:]
    save_json(MEMORY_FILE, memory)


def summarize_memory(memory):
    summary = []
    for src, entries in memory.items():
        total = len(entries)
        fails = len([e for e in entries if not e["success"]])
        summary.append(f"{src}: {fails}/{total} failed restarts")
    return "\n".join(summary)


def main():
    print("🤖 Adaptive Learning Healer (v2) — Online")
    memory = load_json(MEMORY_FILE)
    state = load_json(STATE_FILE)

    while True:
        try:
            errors = fetch_recent_errors()
            services = RENDER_SERVICE_IDS.split(",") if RENDER_SERVICE_IDS else []
            now = datetime.now(timezone.utc)

            if not errors:
                print("✅ System stable.")
                time.sleep(300)
                continue

            for err in errors:
                src = err.get("source", "unknown")
                key = f"{src}_last"
                last_action = state.get(key)
                cooldown_ok = (
                    not last_action
                    or now - datetime.fromisoformat(last_action)
                    > timedelta(minutes=COOLDOWN_MINUTES)
                )

                # analyze historical failure pattern
                past = memory.get(src, [])
                recent_fails = [
                    e for e in past if not e["success"] and
                    datetime.fromisoformat(e["time"]) > now - timedelta(hours=24)
                ]
                if len(recent_fails) >= FAILURE_LIMIT:
                    msg = f"🚫 `{src}` skipped (too many fails in last 24h)"
                    print(msg)
                    send_telegram(msg)
                    continue

                if cooldown_ok:
                    msg = f"🧠 *Adaptive Healer* engaging `{src}`\nDetails: {err['details'][:80]}"
                    send_telegram(msg)
                    success_flag = True
                    for sid in services:
                        feedback = restart_service(sid.strip())
                        print(feedback)
                        send_telegram(feedback)
                        if "❌" in feedback:
                            success_flag = False
                    record_result(memory, src, success_flag)
                    state[key] = now.isoformat()
                    save_json(STATE_FILE, state)
                else:
                    print(f"⏳ Cooldown active for {src}")

            # daily summary (every ~24h)
            if now.hour == 0 and now.minute < 10:
                summary = summarize_memory(memory)
                send_telegram(f"📊 *24h Self-Heal Summary*\n{summary}")

        except Exception as e:
            print("❌ Adaptive Healer error:", e)
            send_telegram(f"⚠️ *Adaptive Healer Error:* {e}")

        time.sleep(300)  # check every 5 min


if __name__ == "__main__":
    main()
