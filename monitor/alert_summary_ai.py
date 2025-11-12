import os
import time
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import requests
from collections import defaultdict
import re

# === Environment Variables ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === Initialize Supabase ===
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# === Helper ===
def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Missing Telegram credentials.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
        print(f"📨 Summary sent: {message[:80]}...")
    except Exception as e:
        print("❌ Telegram send failed:", e)

def categorize_alert(message: str):
    msg = message.lower()
    if any(k in msg for k in ["timeout", "latency", "slow", "delay"]):
        return "⏱️ Performance Issues"
    elif any(k in msg for k in ["error", "failed", "crash", "exception"]):
        return "💥 System Errors"
    elif any(k in msg for k in ["db", "database", "query", "sql"]):
        return "🗄️ Database Alerts"
    elif any(k in msg for k in ["auth", "login", "token"]):
        return "🔑 Authentication Issues"
    elif any(k in msg for k in ["api", "endpoint", "request"]):
        return "🔌 API Warnings"
    else:
        return "📦 Miscellaneous"

def fetch_recent_alerts(limit=50):
    since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    resp = supabase.table("alerts").select("*").gte("created_at", since).limit(limit).execute()
    return resp.data or []

def summarize_alerts(alerts):
    categorized = defaultdict(list)
    for alert in alerts:
        cat = categorize_alert(alert.get("message", ""))
        categorized[cat].append(alert)

    summary_lines = ["🧠 *Hourly AI Summary Report*"]
    for cat, group in categorized.items():
        summary_lines.append(f"\n{cat} — {len(group)} alerts")
        sample_msgs = [f"• {a['message'][:80]}" for a in group[:3]]
        summary_lines.extend(sample_msgs)
    return "\n".join(summary_lines)

def main():
    print("🧠 Smart Summary AI Layer running...")
    while True:
        try:
            alerts = fetch_recent_alerts()
            if alerts:
                summary = summarize_alerts(alerts)
                send_telegram(summary)
            else:
                print("No new alerts to summarize.")
        except Exception as e:
            print("❌ Summary AI error:", e)
        time.sleep(3600)  # runs every hour

if __name__ == "__main__":
    main()
