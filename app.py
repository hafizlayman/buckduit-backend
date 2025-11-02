# file: app.py
from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route("/")
def root():
    return "✅ BuckDuit Backend Online"

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "buckduit-backend",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }), 200


# Optional: add your existing routes below (e.g. /api/offers, /api/alerts)
@app.route("/api/offers")
def offers():
    return jsonify({"message": "offers route active"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
