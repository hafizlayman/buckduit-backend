# ==========================================================
# BuckDuit Backend — Stable Core
# Stage 14.12 Ready (Render + Railway Compatible)
# ==========================================================
from flask import Flask, jsonify
from flask_cors import CORS
import os, sys, time

# ==========================================================
# 1️⃣  PATH FIX — make sure Python can find /services and /utils
# ==========================================================
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ==========================================================
# 2️⃣  Safe logger import (fallback if missing)
# ==========================================================
try:
    from services.utils.ai_logger import log_event
except Exception as e:
    print("⚠️ Logger import failed:", e)
    def log_event(level, source, message, data=None):
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        print(f"[{ts}] [{level}] [{source}] {message}")

# ==========================================================
# 3️⃣  Flask app setup
# ==========================================================
app = Flask(__name__)
CORS(app)
log_event("INFO", "app_boot", "BuckDuit backend initialized.")

# ==========================================================
# 4️⃣  Root Endpoint — sanity check
# ==========================================================
@app.route("/")
def root():
    return jsonify({
        "message": "🧠 BuckDuit AI Core backend is alive!",
        "ok": True
    })

# ==========================================================
# 5️⃣  Health Endpoint
# ==========================================================
@app.route("/api/system/health")
def system_health():
    log_event("INFO", "health", "System health endpoint hit")
    return jsonify({
        "message": "System operational and responding correctly",
        "ok": True,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })

# ==========================================================
# 6️⃣  Example predictive test route (optional)
# ==========================================================
@app.route("/api/predictive/test")
def predictive_test():
    log_event("INFO", "predictive", "Predictive test endpoint hit")
    return jsonify({
        "message": "✅ Predictive test OK",
        "status": "ready"
    })

# ==========================================================
# 7️⃣  App Runner (auto environment)
# ==========================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    env = os.getenv("FLASK_ENV", "development")
    debug = env != "production"
    log_event("INFO", "startup", f"Running Flask on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
