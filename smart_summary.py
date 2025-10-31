import os
import time
import datetime
import pytz
from supabase import create_client, Client
from dotenv import load_dotenv

# ======================================================
# ✅ FIXED ENV LOADER — absolute path + safe override
# ======================================================
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    print(f"✅ Loading environment from: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)
else:
    print("⚠️ .env file not found in backend folder")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Environment variables missing. Here’s what was read:")
    print("SUPABASE_URL =", SUPABASE_URL)
    print("SUPABASE_KEY =", SUPABASE_KEY)
    raise ValueError("⚠️ Missing SUPABASE_URL or SUPABASE_KEY in .env file")

supabase: Client = create_client(SUPABASE_URL.strip(), SUPABASE_KEY.strip())
print("✅ Supabase client initialized successfully.")

# ======================================================
# 🧠 AI Confidence Generator (Mock Simulation)
# ======================================================
def generate_ai_summary():
    offers = [
        {"app": "Upwork", "confidence": 0.72},
        {"app": "Fiverr", "confidence": 0.65},
        {"app": "Respondent.io", "confidence": 0.61},
        {"app": "Clickworker", "confidence": 0.52},
        {"app": "Toloka", "confidence": 0.45},
        {"app": "Remotasks", "confidence": 0.41},
        {"app": "Vase.ai", "confidence": 0.38},
    ]

    avg_confidence = sum(o["confidence"] for o in offers) / len(offers)

    summary_text = "📊 BuckDuit AI Summary Report — {}\n\n".format(
        datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
    )

    high = [f"• {o['app']} = {o['confidence']}" for o in offers if o["confidence"] >= 0.7]
    med = [f"• {o['app']} = {o['confidence']}" for o in offers if 0.5 <= o["confidence"] < 0.7]
    low = [f"• {o['app']} = {o['confidence']}" for o in offers if o["confidence"] < 0.5]

    if high:
        summary_text += "🔥 High (≥0.7):\n" + "\n".join(high) + "\n"
    if med:
        summary_text += "⚖️ Medium (0.5–0.7):\n" + "\n".join(med) + "\n"
    if low:
        summary_text += "❄️ Low (<0.5):\n" + "\n".join(low) + "\n"

    summary_text += f"\n🟩 Avg Confidence: {avg_confidence:.2f}\n📊 Heatmap: 🟨🟧🟥🟥🟥\nNext update = 5 minutes."

    print("✅ Summary generated successfully.")
    return summary_text, avg_confidence


# ======================================================
# 🪵 LOG REPORT TO SUPABASE (auto insert)
# ======================================================
def log_to_supabase(summary_text, avg_confidence):
    try:
        response = (
            supabase.table("report_logs")
            .insert(
                {
                    "report_type": "ai_summary",
                    "content": summary_text,
                    "avg_confidence": avg_confidence,
                    "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
                }
            )
            .execute()
        )
        print("✅ Logged to report_logs table.")
        return response
    except Exception as e:
        print("⚠️ Could not log to report_logs:", e)
        return None


# ======================================================
# 🧩 MAIN SCHEDULER LOOP — runs every 5 minutes
# ======================================================
if __name__ == "__main__":
    while True:
        summary_text, avg_confidence = generate_ai_summary()
        log_to_supabase(summary_text, avg_confidence)
        time.sleep(300)  # every 5 minutes
