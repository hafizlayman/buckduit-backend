#!/bin/bash
echo "🚀 Starting BuckDuit AI Core..."
export PORT=${PORT:-10000}

# Safety: wait for environment to load
sleep 3

# Run Flask app through Gunicorn
exec gunicorn --workers=1 --timeout 120 --bind 0.0.0.0:$PORT buckduit_ai_core:app
