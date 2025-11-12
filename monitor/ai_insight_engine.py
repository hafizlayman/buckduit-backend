import os, time, statistics, requests
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from collections import defaultdict
import openai   # Requires OPENAI_API_KEY env var

# === Environment ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
openai.api_key = OPENAI_API_KEY

# === Helpers ===
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10,
        )
        print("📨 Insight sent to Telegram.")
    except Exception as e:
        print("❌ Telegram failed:", e)

def fetch_alerts(hours_back=2):
    since = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()
    res = supabase.table("alerts").select("*").gte("created_at", since).execute()
    return res.data or []

def compute_metrics(alerts):
    buckets = defaultdict(list)
    for a in alerts:
        msg = (a.get("message") or "").lower()
        sev = a.get("severity", "INFO")
        if "api" in msg or "request" in msg:
            buckets["api"].append(sev)
        elif "db" in msg or "database" in msg:
            buckets["db"].append(sev)
        elif "auth" in msg or "token" in msg:
            buckets["auth"].append(sev)
        elif "latency" in msg or "timeout" in msg:
            buckets["latency"].append(sev)
        else:
            buckets["other"].append(sev)
    return {k: len(v) for k, v in buckets.items()}

def detect_anomalies(curr, prev):
    deltas = {}
    for k in curr:
        old = prev.get(k, 0)
        new = curr[k]
        if old == 0 and new > 0:
            deltas[k] = "+∞"
        elif old > 0:
            change = ((new - old) / old) * 100
            if abs(change) >= 30:
                deltas[k] = f"{change:+.1f}%"
    return deltas

def ai_generate_summary(curr_metrics, deltas):
    prompt = (
        "You are a system health analyst. Given current alert metrics and percentage "
        "changes, write a concise Markdown summary for Telegram.\n\n"
        f"Current metrics: {curr_metrics}\n"
        f"Detected changes: {deltas}\n\n"
        "Highlight anomalies, possible causes, and end with 1 short actionable tip."
    )
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
        )
        return resp.choices[0].message["content"].strip()
    except Exception as e:
        print("❌ AI generation failed:", e)
        return None

def main():
    print("🤖 AI Insight Engine active...")
    prev_metrics = {}
    while True:
        try:
            alerts = fetch_alerts()
            cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
            prev = [a for a in alerts if a["created_at"] < cutoff.isoformat()]
            curr = [a for a in alerts if a["created_at"] >= cutoff.isoformat()]

            prev_metrics = compute_metrics(prev)
            curr_metrics = compute_metrics(curr)
            deltas = detect_anomalies(curr_metrics, prev_metrics)

            if deltas:
                ai_summary = ai_generate_summary(curr_metrics, deltas)
                if ai_summary:
                    send_telegram(f"🧩 *AI Insight Report*\n\n{ai_summary}")
            else:
                print("No significant anomalies.")
        except Exception as e:
            print("❌ Engine error:", e)

        time.sleep(3600)  # run hourly

if __name__ == "__main__":
    main()
