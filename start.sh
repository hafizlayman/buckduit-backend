#!/usr/bin/env bash
set -e

echo "======================================"
echo "🚀 Starting BuckDuit API + AI Core Worker"
echo "======================================"

# --- Force install dependencies (even if Render skipped) ---
echo "Installing project dependencies..."
python -m ensurepip --upgrade
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt

# --- Safety: ensure gunicorn present ---
pip install --no-cache-dir gunicorn

# --- Optional check ---
pip list | grep -E "Flask|gunicorn" || echo "⚠️ Flask or Gunicorn not found!"

# --- Start AI Core Worker in background ---
echo "Starting background AI Core worker..."
python -u buckduit_ai_core.py &

# --- Launch Flask API with gunicorn ---
echo "Starting Flask API server..."
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0
