import os
from supabase import create_client, Client

def get_supabase() -> Client | None:
    """Returns a connected Supabase client or None if credentials invalid."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        print("❌ Missing Supabase credentials.")
        return None

    key = key.strip()
    if len(key) < 40:
        print("❌ Supabase key too short — likely truncated.")
        return None

    try:
        sb = create_client(url, key)
        print("✅ Supabase client initialized successfully.")
        return sb
    except Exception as e:
        print(f"❌ Supabase init failed: {e}")
        return None
