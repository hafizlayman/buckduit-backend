# ==========================================================
# BuckDuit Backend — Stage 14.12.20 (Auto-Heal Entrypoint)
# ==========================================================
from flask import Flask, jsonify
from flask_cors import CORS
import os, time, traceback
from supabase import create_client
from dotenv import load_dotenv

def load_environment():
    """Try multiple .env fallbacks (Railway + local)"""
    for candidate in [".env.prod", ".env.stage", ".env", "/app/backend/.env", "/app/.env"]:
        if os.path.exists(candidate):
            load_dotenv(candidate)
            print(f"✅ Loaded environment from {candidate}")
            return
    print("⚠️ No .env file found — using Railway service vars")

load_environment()

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized.")
    else:
        print("⚠️ Missing Supabase credentials.")
except Exception as e:
    print("❌ Supabase init error:", e)
    traceback.print_exc()

@app.route("/")
@app.route("/health")
def health():
    return jsonify({
        "status": "ok" if supabase else "partial",
        "supabase_connected": bool(supabase)
    }), 200

if __name__ == "__main__":
    try:
        port = int(os.getenv("PORT", 5000))
        print(f"🚀 Running BuckDuit backend on port {port}")
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        print("💥 Flask crashed:", e)
        traceback.print_exc()
        time.sleep(10)
