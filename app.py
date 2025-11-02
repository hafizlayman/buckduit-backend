import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from supabase import create_client, Client

# --- Force Load .env (Windows-safe) ---
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print(f"❌ .env file not found at: {env_path}")

print("🔍 DEBUG: SUPABASE_URL =", os.getenv("SUPABASE_URL"))
print("🔍 DEBUG: SUPABASE_SERVICE_KEY =", "Loaded ✅" if os.getenv("SUPABASE_SERVICE_KEY") else "Missing ❌")

# --- Initialize Flask ---
app = Flask(__name__)
CORS(app)

# --- Initialize Supabase ---
def init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )

    if not url or not key:
        print(f"❌ Supabase not initialized. URL={url}, KEY={bool(key)}")
        return None

    try:
        client = create_client(url, key)
        print("✅ Supabase client initialized successfully.")
        return client
    except Exception as e:
        print(f"❌ Error initializing Supabase: {e}")
        return None

supabase = init_supabase()

# --- Routes ---
@app.route("/healthz")
def health_check():
    return jsonify({"status": "ok"}), 200


@app.route("/api/offers", methods=["GET"])
def get_offers():
    if not supabase:
        return jsonify({"error": "Supabase not connected"}), 500

    try:
        table_name = os.getenv("SUPABASE_TABLE", "offers")
        data = supabase.table(table_name).select("*").execute()
        items = data.data if data and hasattr(data, "data") else []
        return jsonify({"items": items}), 200
    except Exception as e:
        print(f"❌ Error fetching offers: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/summary-card", methods=["GET"])
def summary_card():
    try:
        stats = {
            "total_offers": 42,
            "top_category": "Freelance",
            "ai_confidence": 0.91
        }
        return jsonify(stats), 200
    except Exception as e:
        print(f"❌ Error generating summary card: {e}")
        return jsonify({"error": str(e)}), 500


# --- Entry Point ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
