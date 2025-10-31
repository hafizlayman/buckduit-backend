#!/usr/bin/env bash
echo "============================================"
echo "🚀 Starting BuckDuit API + AI Core Worker..."
echo "============================================"

# Run both Flask API + AI Core in background
python -u buckduit_ai_core.py &

# Start Flask API using gunicorn safely
python -m gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0
