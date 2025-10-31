#!/usr/bin/env bash
set -e

echo "========================================"
echo "🚀 Starting BuckDuit API + AI Core Worker"
echo "========================================"

# --- Install missing runtime dependencies ---
echo "Installing pip + gunicorn at runtime..."
python -m ensurepip --upgrade
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir gunicorn

# --- Optional: verify installation ---
pip show gunicorn || echo "⚠️ Gunicorn still not found!"

# --- Start AI Core worker in background ---
python -u buckduit_ai_core.py &

# --- Launch Flask API via gunicorn ---
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0
