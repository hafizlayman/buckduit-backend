# ==========================================================
# BuckDuit Backend — Stage 14.13.3 (Stable Heartbeat)
# ==========================================================
from flask import Flask, jsonify
from flask_cors import CORS
from supabase import create_client
import os

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
PORT = int(os.getenv("PORT", 5000))

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected")
    except Exception as e:
        print("⚠️ Supabase connection failed:", e)
else:
    print("⚠️ Missing Supabase credentials")

@app.route("/health")
def health():
    return jsonify({"status": "ok", "msg": "BuckDuit backend operational"}), 200

if __name__ == "__main__":
    print(f"🚀 Running Flask on 0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT)
