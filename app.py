import os
from flask import Flask, jsonify
from supabase import create_client, Client

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase client initialized successfully.")
    except Exception as e:
        print("❌ Failed to initialize Supabase:", str(e))
else:
    print("⚠️ Missing Supabase credentials in environment.")

@app.route("/")
def home():
    return jsonify({"message": "✅ BuckDuit AI Core backend is alive!"})

@app.route("/api/alerts/summary-card")
def summary_card():
    if not supabase:
        return jsonify({"error": "Supabase client not initialized"}), 500
    try:
        result = supabase.table("alerts").select("*").order("created_at", desc=True).limit(5).execute()
        return jsonify(result.data)
    except Exception as e:
        print("❌ Error fetching alerts:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
