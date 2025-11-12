# =========================================
# backend/config/env_loader.py
# BuckDuit Environment Loader — Stable v14.01
# =========================================
import os
from dotenv import load_dotenv

def load_environment():
    """
    Loads the correct .env file based on APP_ENV.
    Automatically validates key variables.
    """

    env = os.getenv("APP_ENV", "dev").lower()
    env_file = f".env.{env}"

    if not os.path.exists(env_file):
        print(f"⚠️ No {env_file} found — falling back to .env")
        env_file = ".env"

    load_dotenv(env_file)
    print(f"🌍 Environment loaded: {env.upper()} ({env_file})")

    # Quick validation
    supa_url = os.getenv("SUPABASE_URL", "").strip()
    supa_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

    if not supa_url or not supa_key:
        print("❌ Missing Supabase credentials in environment file.")
    elif len(supa_key) < 100:
        print(f"❌ Supabase key too short ({len(supa_key)} chars) — invalid or truncated.")
    else:
        print("✅ Environment keys detected (Supabase loaded OK).")
