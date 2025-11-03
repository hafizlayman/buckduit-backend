#!/bin/bash
set -e

echo "==========================================="
echo "🚀 Launching BuckDuit AI Core (Production)"
echo "==========================================="

# Verify working directory
echo "📂 Current directory: $(pwd)"

# Verify Python version
python --version

# Environment check
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_KEY" ]; then
  echo "⚠️  Warning: Missing Supabase environment variables!"
  echo "SUPABASE_URL=$SUPABASE_URL"
  echo "SUPABASE_SERVICE_KEY (first 10 chars): ${SUPABASE_SERVICE_KEY:0:10}..."
else
  echo "✅ Supabase variables detected."
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

# Show all installed packages (optional debug)
pip freeze | grep flask
pip freeze | grep gunicorn
pip freeze | grep supabase

# Start Gunicorn server and bind to Railway port
echo "🚀 Starting Gunicorn with buckduit_ai_core:app ..."
exec gunicorn buckduit_ai_core:app \
  --workers 2 \
  --threads 2 \
  --timeout 120 \
  --bind 0.0.0.0:${PORT:-8080} \
  --log-level info \
  --access-logfile '-' \
  --error-logfile '-'
