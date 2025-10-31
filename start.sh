#!/bin/bash
# Combined startup for BuckDuit API + AI Core
# Keeps both processes alive in Render's single service

echo "============================================"
echo "🚀 Starting BuckDuit API + AI Core Worker..."
echo "============================================"

# Start AI Core in background
python buckduit_ai_core.py &

# Start Flask API using Gunicorn on Render's assigned port
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
