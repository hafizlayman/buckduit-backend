import os
from config.env_loader import load_environment

load_environment()

print("\n🔍 DEBUG: Environment Variables Snapshot")
print("----------------------------------------")
print("APP_ENV =", os.getenv("APP_ENV"))
print("SUPABASE_URL =", os.getenv("SUPABASE_URL"))
print("SERVICE_KEY length =", len(os.getenv("SUPABASE_SERVICE_KEY") or ""))
print("SERVICE_KEY first 40 chars:", (os.getenv("SUPABASE_SERVICE_KEY") or "")[:40])
