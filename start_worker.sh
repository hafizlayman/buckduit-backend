#!/bin/bash
echo "🚀 Booting BuckDuit Backend (Keep-Alive Mode)..."

PORT=${PORT:-5000}

echo "🌐 Starting Flask backend on port $PORT..."
python3 backend/app.py --port=$PORT &

echo "🧠 Starting BuckDuit AI Scheduler..."
python3 -m backend.services.workers.scheduler &

echo "⏳ All services launched. Keeping container alive..."
tail -f /dev/null
