from supabase import create_client, Client
import os

# --- Safe, universal Supabase initializer ---
def init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )
    if not url or not key:
        print("❌ Supabase not initialized — missing URL or Key")
        return None
    try:
        client = create_client(url, key)
        print("✅ Supabase client initialized successfully.")
        return client
    except Exception as e:
        print(f"❌ Supabase init error: {e}")
        return None

supabase = init_supabase()
