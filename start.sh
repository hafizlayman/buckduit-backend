#!/bin/sh
set -e

echo "🏁 BuckDuit — Start Script (Stage 14.15)"

export PYTHONUNBUFFERED=1

# --- sanity echo ---
python --version || true
pip --version || true

# -------- Launch Flask (foreground) --------
echo "🌐 Launching Flask..."
# run the daemon in background *before* Flask so it can attach
python -u supervisor_daemon.py &

# (If you also run heartbeat worker separately, keep it here too)
# python -u heartbeat_ai.py &   # <-- if you had this in Stage 14.13

# Finally run Flask (foreground keeps container alive)
python -u app.py
