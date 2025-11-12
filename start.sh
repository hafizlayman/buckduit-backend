#!/bin/sh
set -e

echo "🚀 BuckDuit — Stage 14.13.6 (Root Entrypoint Auto-Fix)"
echo "📂 Current Directory:"
pwd
echo "📦 Listing structure:"
ls -R

# ==========================================================
# 1️⃣ Auto-detect Flask app file
# ==========================================================
if [ -f "./app.py" ]; then
  echo "✅ Found app.py at root"
  APP_PATH="./app.py"
elif [ -f "./backend/app.py" ]; then
  echo "✅ Found backend/app.py"
  APP_PATH="./backend/app.py"
else
  echo "❌ ERROR: app.py not found in root or backend"
  ls
  exit 1
fi

# ==========================================================
# 2️⃣ Start Flask Backend
# ==========================================================
echo "🌐 Launching Flask from: $APP_PATH ..."
python3 $APP_PATH &

# ==========================================================
# 3️⃣ Start Heartbeat AI (optional)
# ==========================================================
if [ -f "./backend/workers/heartbeat_ai.py" ]; then
  echo "🫀 Launching Heartbeat AI..."
  python3 ./backend/workers/heartbeat_ai.py &
else
  echo "⚠️ Skipping Heartbeat AI (file not found)"
fi

# ==========================================================
# 4️⃣ Keep Container Alive
# ==========================================================
echo "♻️ Keepalive loop started..."
while true; do
  ps aux | grep "python3" | grep -v "grep" || echo "⚠️ Warning: No python process running!"
  sleep 30
done
