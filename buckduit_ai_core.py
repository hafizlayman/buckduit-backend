import os, threading, time, datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import traceback

# =====================================================
# 🧠 BuckDuit AI Core — Unified Orchestration Script
# =====================================================

# 1️⃣ Load environment
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Missing SUPABASE_URL or SUPABASE_KEY in .env file")

# 2️⃣ Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Supabase client initialized successfully.")

# 3️⃣ Detect available columns (safe auto-detect)
try:
    meta = supabase.table("offers").select("*").limit(1).execute()
    sample = meta.data[0] if meta.data else {}
    confidence_key = None
    for key in ["ai_confidence", "confidence", "avg_confidence"]:
        if key in sample:
            confidence_key = key
            break
    if not confidence_key:
        raise KeyError("No confidence-related column found.")
    print(f"✅ Using confidence column: {confidence_key}")
except Exception as e:
    print(f"⚠️ Could not detect column: {e}")
    confidence_key = "ai_confidence"

# 4️⃣ Check report_logs table
try:
    supabase.table("report_logs").select("*").limit(1).execute()
    print("✅ report_logs table accessible.")
except Exception as e:
    print(f"⚠️ report_logs not accessible: {e}")

# =====================================================
# 🧩 Utility: Telegram send (stub placeholder)
# =====================================================
def send_telegram_message(message: str):
    print(f"📨 Telegram message:\n{message}\n")
    # (Later replace with requests.post to Telegram Bot API)
    return True

# =====================================================
# 🧩 AI Summary Generator
# =====================================================
def generate_ai_summary():
    try:
        res = supabase.table("offers").select("*").execute()
        rows = res.data
        if not rows:
            raise ValueError("No offers data found.")

        # Filter confidence values
        conf_values = []
        for r in rows:
            val = r.get(confidence_key)
            if val is not None:
                try:
                    conf_values.append(float(val))
                except:
                    pass

        if not conf_values:
            raise ValueError("No numeric confidence values found.")

        avg_conf = sum(conf_values) / len(conf_values)

        # Grouping logic
        high = [r for r in rows if r.get(confidence_key) and float(r.get(confidence_key)) >= 0.7]
        low = [r for r in rows if r.get(confidence_key) and float(r.get(confidence_key)) < 0.5]

        def lines(data):
            if not data:
                return "• —"
            parts = []
            for r in data:
                name = r.get("name") or r.get("app_name") or "N/A"
                try:
                    conf = float(r.get(confidence_key))
                    parts.append(f"• {name} = {conf:.2f}")
                except:
                    pass
            return "\n".join(parts) if parts else "• —"

        summary = (
            f"🧠 <b>BuckDuit AI Summary Report</b>\n"
            f"📅 {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"🔥 <b>High (≥0.7)</b>:\n{lines(high)}\n\n"
            f"🧊 <b>Low (&lt;0.5)</b>:\n{lines(low)}\n\n"
            f"📊 Average confidence: {avg_conf:.2f}"
        )
        return summary, avg_conf

    except Exception as e:
        print(f"❌ generate_ai_summary() failed: {e}")
        traceback.print_exc()
        return None, None

# =====================================================
# 🧩 Summary Worker (auto-retry logging)
# =====================================================
class SummaryWorker(threading.Thread):
    def run(self):
        print("🚀 SummaryWorker started.")
        while True:
            text, avg = generate_ai_summary()
            if not text:
                print("⚠️ Skipped empty summary.")
                time.sleep(300)
                continue

            print(text)
            send_telegram_message(text)

            if supabase:
                try:
                    supabase.table("report_logs").insert({
                        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "summary_text": text,
                        "avg_confidence": avg
                    }).execute()
                    print("✅ Summary logged.")
                except Exception as e:
                    msg = str(e)
                    if "schema cache" in msg or "PGRST204" in msg:
                        print("⚠️ Supabase cache not updated — retrying in 30s...")
                        time.sleep(30)
                        try:
                            supabase.table("report_logs").insert({
                                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                "summary_text": text,
                                "avg_confidence": avg
                            }).execute()
                            print("✅ Summary logged on retry.")
                        except Exception as e2:
                            print(f"❌ Retry failed: {e2}")
                    else:
                        print(f"⚠️ Logging failed: {e}")
            time.sleep(300)  # every 5 min

# =====================================================
# 🧩 Adaptive Monitor
# =====================================================
class AdaptiveMonitor(threading.Thread):
    def run(self):
        print("🚀 AdaptiveMonitor started.")
        last_conf = None
        while True:
            _, now_avg = generate_ai_summary()
            if now_avg is None:
                time.sleep(180)
                continue

            if last_conf is not None:
                diff = now_avg - last_conf
                if abs(diff) >= 0.1:
                    trend = "UP" if diff > 0 else "DOWN"
                    msg = (
                        f"⚡ <b>AI Confidence {trend}</b>\n"
                        f"Prev: {last_conf:.2f} → Now: {now_avg:.2f}\n"
                        f"Change: {diff:+.2f}"
                    )
                    send_telegram_message(msg)
            last_conf = now_avg
            time.sleep(180)  # every 3 min

# =====================================================
# 🧩 Telegram Poller (placeholder)
# =====================================================
class TelegramPoller(threading.Thread):
    def run(self):
        print("🚀 TelegramPoller started (idle placeholder).")
        while True:
            time.sleep(60)

# =====================================================
# 🧩 Main Loop
# =====================================================
def main():
    print("🧠 BuckDuit AI Core starting…")
    SummaryWorker().start()
    AdaptiveMonitor().start()
    TelegramPoller().start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("👋 Shutting down by user…")

if __name__ == "__main__":
    main()
