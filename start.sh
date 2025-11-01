#!/bin/bash
echo "🚀 Starting BuckDuit AI Core..."
export PORT=${PORT:-8080}

# Wait for envs to load
sleep 2

# Start Flask app through Gunicorn
exec gunicorn --workers=1 --timeout 120 --bind 0.0.0.0:$PORT buckduit_ai_core:app
