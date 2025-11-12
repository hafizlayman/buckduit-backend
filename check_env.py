import os
from dotenv import load_dotenv

env_file = ".env.dev"
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ Loaded environment: {env_file}")
else:
    print(f"❌ {env_file} not found")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    print("🔗 Supabase URL:", SUPABASE_URL)
    print("🔑 Key length:", len(SUPABASE_KEY))
    print("First 10 chars:", SUPABASE_KEY[:10])
    print("Last 10 chars:", SUPABASE_KEY[-10:])
else:
    print("⚠️ Missing Supabase credentials in environment.")
