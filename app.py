# ==========================================================
# BuckDuit Backend — Stage 14.14 Stable Flask Entrypoint
# ==========================================================
from flask import Flask, jsonify
from flask_cors import CORS
from supabase import create_client
import os

# Initialize Flask
app = Flask(__name__)
CORS(app)

# ==========================================================
# 1️⃣ Environment Setup
# ==========================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
PORT = int(os.getenv("PORT", 5000))

# ==========================================================
# 2️⃣ Supabase Connection
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
# 3️⃣ Routes
# ==========================================================
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "BuckDuit backend running successfully",
        "env": os.getenv("APP_ENV", "production")
    }), 200


@app.route("/")
def root():
    return jsonify({"msg": "🚀 BuckDuit API Live"}), 200

# ==========================================================
# 4️⃣ Run
# ==========================================================
if __name__ == "__main__":
    print(f"🌐 Running Flask on 0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT)
