#!/bin/bash
# ==============================================
# 🚀 BuckDuit AI Core - Railway Production Launcher
# ==============================================

set -e

echo "============================================="
echo "🔧 Starting BuckDuit AI Core"
echo "📦 Python Version: $(python3 --version)"
echo "🌍 Working Directory: $(pwd)"
echo "⚙️ PORT: ${PORT}"
echo "============================================="

ls -la

# ✅ Safety: Change to correct directory if needed
if [ -f "backend/buckduit_ai_core.py" ]; then
  echo "📂 Switching to backend directory..."
  cd backend
fi

# ✅ Activate venv (optional)
if [ -d "venv" ]; then
  echo "✅ Activating virtual environment..."
  source venv/bin/activate
fi

echo "📦 Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "🧠 Checking Flask app..."
python3 - <<'PYCODE'
import importlib
try:
    m = importlib.import_module("buckduit_ai_core")
    if hasattr(m, "app"):
        print("✅ Flask app found: buckduit_ai_core.app")
    else:
        print("❌ Flask app missing inside buckduit_ai_core.py")
except Exception as e:
    print(f"❌ Import failed: {e}")
PYCODE

echo "🚀 Launching Gunicorn..."
exec gunicorn buckduit_ai_core:app \
  --workers 1 \
  --threads 2 \
  --timeout 120 \
  --bind 0.0.0.0:${PORT} \
  --preload \
  --log-level debug
