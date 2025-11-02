# 🧠 BuckDuit AI Core
# Version: Stage 13.34 — Clean Railway Worker Build
# -----------------------------------------------
# This worker handles background AI tasks, Supabase monitoring, and Telegram polling.
# It is designed to run continuously in Railway as a background service.

import os
import time
from supabase import create_client, Client
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

# --- Initialize Supabase Client ---
def init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )

    if not url or not key:
        print(f"❌ Supabase not initialized. URL={url}, KEY={bool(key)}")
        return None

    try:
        client = create_client(url, key)
        print("✅ Supabase client initialized successfully.")
        return client
    except Exception as e:
        print(f"❌ Error initializing Supabase: {e}")
        return None

# --- Create global client ---
supabase = init_supabase()

# --- Placeholder logic for background tasks ---
def run_background_tasks():
    """
    This function simulates the background AI/monitor logic.
    You can later import your real modules:
        from adaptive_alerts import start_alert_monitor
        from smart_summary import generate_ai_summary
    """
    print("🚀 BuckDuit AI Core worker running main loop...", flush=True)
    while True:
        # TODO: integrate SummaryWorker, AdaptiveMonitor, TelegramPoller
        # Example:
        #   generate_ai_summary()
        #   start_alert_monitor()
        time.sleep(30)  # Keeps Railway process alive


# --- Main Entrypoint ---
if __name__ == "__main__":
    print("🧠 BuckDuit AI Core starting…", flush=True)

    if supabase is None:
        print("⚠️ Worker stopped: Supabase connection not initialized.")
    else:
        run_background_tasks()
