#!/bin/sh
set -e

echo "🚀 BuckDuit — Universal Entrypoint (Stage 14.13.4)"
echo "📂 Current Directory:"
pwd
echo "📦 Listing structure:"
ls -R

# Auto-detect backend/app.py path
if [ -f "backend/app.py" ]; then
  echo "✅ Found backend/app.py"
  APP_PATH="backend/app.py"
elif [ -f "app.py" ]; then
  echo "✅ Found app.py at root"
  APP_PATH="app.py"
else
  echo "❌ ERROR: Could not find app.py"
  exit 1
fi

echo "🌐 Launching Flask: $APP_PATH ..."
python3 $APP_PATH &

# Launch heartbeat if present
if [ -f "backend/workers/heartbeat_ai.py" ]; then
  echo "🫀 Launching Heartbeat AI..."
  python3 backend/workers/heartbeat_ai.py &
fi

echo "✅ All services started. Entering keepalive..."
while true; do
  ps aux | grep "python3" | grep -v "grep"
  sleep 30
done
