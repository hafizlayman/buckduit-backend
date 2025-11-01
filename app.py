import os
from flask import Flask, jsonify
from supabase import create_client, Client

app = Flask(__name__)

# ✅ Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# ✅ Safety guard to catch missing keys cleanly
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing Supabase credentials.")
    @app.route("/")
    def fail():
        return jsonify({"error": "Supabase credentials missing"}), 500
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("✅ Supabase client initialized successfully.")

    @app.route("/")
    def root():
        return jsonify({"message": "BuckDuit AI Core running."})

    @app.route("/api/alerts/summary-card")
    def summary_card():
        try:
            data = supabase.table("alerts").select("*").limit(5).execute()
            return jsonify(data.data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
