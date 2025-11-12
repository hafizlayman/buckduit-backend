#!/bin/bash
set -e

echo "🚀 BuckDuit — Railway Entrypoint Fix"
PORT=${PORT:-5000}

echo "🧠 Checking backend path..."
if [ ! -d "backend" ]; then
  echo "⚠️ Missing backend folder, creating soft link..."
  mkdir -p backend
  cp -r ./* backend/ || true
fi

echo "🌐 Launching Flask..."
python3 backend/app.py &

FLASK_PID=$!
sleep 2

if ps -p $FLASK_PID > /dev/null; then
  echo "✅ Flask started successfully (PID: $FLASK_PID)"
else
  echo "❌ Flask failed to start."
  exit 1
fi

echo "🔁 Keepalive loop started..."
while true; do
  if ! ps -p $FLASK_PID > /dev/null; then
    echo "💥 Flask exited. Restarting..."
    python3 backend/app.py &
    FLASK_PID=$!
  fi
  sleep 10
done
