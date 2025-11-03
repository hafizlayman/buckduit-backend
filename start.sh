#!/bin/bash
# ==============================================
# 🚀 BuckDuit AI Core - Stable Railway Start Script
# ==============================================

set -e  # Exit immediately if a command fails

echo "============================================="
echo "🔧 Starting BuckDuit AI Core"
echo "📦 Python Version: $(python3 --version)"
echo "🌍 Working Directory: $(pwd)"
echo "⚙️  PORT: ${PORT}"
echo "============================================="

# Show files in current directory for debugging
ls -la

# Activate virtual environment if it exists
if [ -d "venv" ]; then
  echo "✅ Activating virtual environment..."
  source venv/bin/activate
else
  echo "⚠️ No virtual environment detected. Using system Python."
fi

# Ensure dependencies are installed
echo "📦 Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

# Verify that buckduit_ai_core.py exists
if [ ! -f "buckduit_ai_core.py" ]; then
  echo "❌ Error: buckduit_ai_core.py not found in $(pwd)"
  exit 1
fi

# Verify that Flask app variable exists
echo "🧠 Verifying Flask app import..."
python3 - <<'PYCODE'
import importlib
try:
    module = importlib.import_module("buckduit_ai_core")
    if hasattr(module, "app"):
        print("✅ Flask app found: buckduit_ai_core.app")
    else:
        print("❌ Flask app variable missing inside buckduit_ai_core.py")
except Exception as e:
    print(f"❌ Import failed: {e}")
PYCODE

# Start Gunicorn using Railway's PORT
echo "🚀 Launching Gunicorn..."
exec gunicorn buckduit_ai_core:app \
  --workers 1 \
  --threads 2 \
  --timeout 120 \
  --bind 0.0.0.0:${PORT} \
  --preload \
  --log-level debug
