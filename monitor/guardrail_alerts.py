# ==========================================================
# guardrail_alerts.py — Stage 14.07
# Auto-alerts for Bias & Drift Guardrails (Telegram + Supabase)
# ==========================================================
import os, time, requests
from supabase import create_client
from datetime import datetime, timezone

# ── Setup Telegram + Supabase ─────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ guardrail_alerts: Supabase connected")
    except Exception as e:
        print("⚠️ guardrail_alerts: Supabase init failed:", e)

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:5000")

# ── Telegram sender ───────────────────────────────────────
def send_telegram(msg: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram creds missing; skipping alert.")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        print("⚠️ Telegram send failed:", e)

# ── Bias/Drift monitor loop ───────────────────────────────
def check_guardrails():
    """Poll both bias and drift endpoints and fire alerts if breached."""
    try:
        bias = requests.get(f"{API_BASE}/api/predictive/bias-check?alpha=0.35&threshold=0.12").json()
        drift = requests.get(f"{API_BASE}/api/predictive/live-smooth?alpha=0.35&step=5").json()
    except Exception as e:
        print("❌ guardrail check failed:", e)
        return

    alerts = []
    # Bias breach
    if bias.get("flagged") or abs(bias.get("bias_abs_max", 0)) > bias.get("threshold", 0.12):
        alerts.append(f"⚠️ Bias Guardrail Breach\nAbsBias={bias.get('bias_abs_max'):.4f} > {bias.get('threshold')}")
    # Drift abnormality
    if drift.get("ok") and isinstance(drift.get("data"), list):
        last = drift["data"][-1]
        if abs(last.get("smoothed_drift", 0)) > 0.15:
            alerts.append(f"⚠️ Drift Spike\nSmoothedDrift={last['smoothed_drift']:.4f}")

    if not alerts:
        print("✅ guardrail_alerts: all within range.")
        return

    for msg in alerts:
        timestamp = datetime.now(timezone.utc).isoformat()
        print("🚨", msg)
        send_telegram(msg)
        if supabase:
            try:
                supabase.table("predictive_alerts").insert({
                    "timestamp": timestamp,
                    "message": msg,
                    "bias_max": bias.get("bias_abs_max"),
                    "threshold": bias.get("threshold"),
                    "flagged": bias.get("flagged"),
                }).execute()
            except Exception as e:
                print("⚠️ failed to log alert:", e)

# ── Main loop ─────────────────────────────────────────────
if __name__ == "__main__":
    print("🧠 guardrail_alerts daemon started (interval=60s)")
    while True:
        check_guardrails()
        time.sleep(60)
