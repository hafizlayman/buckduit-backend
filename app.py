# ==========================================================
# BuckDuit Backend — Stage 14.15
# Drift Forecast Supervisor + Telegram Notifier Integration
# ==========================================================

from flask import Flask, jsonify
from flask_cors import CORS
import os
import time

# Optional logging (safe fallback if utils/ai_logger.py missing)
try:
    from utils.ai_logger import log_event
except Exception:
    def log_event(*args, **kwargs):
        pass


# ==========================================================
# 1️⃣  Flask Initialization
# ==========================================================
app = Flask(__name__)
CORS(app)

SERVICE_NAME = os.getenv("SERVICE_NAME", "buckduit-backend")
APP_ENV = os.getenv("APP_ENV", "production")


# ==========================================================
# 2️⃣  Health + Root Routes
# ==========================================================
@app.route("/")
def root():
    """Public base endpoint for quick check"""
    return jsonify({"msg": "🚀 BuckDuit API Live"})

@app.route("/health")
def health():
    """Health monitor endpoint"""
    return jsonify({
        "status": "ok",
        "message": f"{SERVICE_NAME} backend running successfully",
        "env": APP_ENV
    })


# ==========================================================
# 3️⃣  Blueprint Imports (Keep Adding Here)
# ==========================================================
try:
    # Import the new Drift Forecast Supervisor Blueprint
    from routes.drift_routes import drift_bp
    app.register_blueprint(drift_bp)
    log_event("drift_routes_registered", True)
except Exception as e:
    log_event("drift_routes_error", str(e))
    print(f"⚠️ Drift blueprint not loaded: {e}")


# ==========================================================
# 4️⃣  Error Handlers
# ==========================================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not Found", "path": str(e)}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


# ==========================================================
# 5️⃣  Main Entrypoint
# ==========================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Starting {SERVICE_NAME} on port {port}...")
    app.run(host="0.0.0.0", port=port)
