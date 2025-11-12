# ==========================================================
# BuckDuit Backend — Stage 14.13.6 (Stable Root Entrypoint)
# ==========================================================
from flask import Flask, jsonify
from flask_cors import CORS
from supabase import create_client
import os

# ==========================================================
# 1️⃣ Initialize Flask
# ==========================================================
app = Flask(__name__)
CORS(app)

# ==========================================================
# 2️⃣ Environment Variables
# ==========================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
PORT = int(os.getenv("PORT", 5000))

# ==========================================================
# 3️⃣ Connect to Supabase
# ==========================================================
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected successfully")
    except Exception as e:
        print("⚠️ Supabase connection failed:", e)
else:
    print("⚠️ Missing Supabase credentials")

# ==========================================================
# 4️⃣ Health Route
# ==========================================================
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "BuckDuit backend running successfully",
        "env": os.getenv("APP_ENV", "production")
    }), 200

# ==========================================================
# 5️⃣ Run App
# ==========================================================
if __name__ == "__main__":
    print(f"🚀 Starting Flask on 0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT)
