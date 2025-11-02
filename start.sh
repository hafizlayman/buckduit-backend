#!/usr/bin/env bash
set -euo pipefail
cmd="${1:-}"

build() {
  echo "[build] Installing requirements..."
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
  echo "[build] Done."
}

run_web() {
  : "${PORT:?Render did not set PORT}"
  echo "[web] Starting Gunicorn on port ${PORT}"
  exec gunicorn app:app \
    --bind 0.0.0.0:"${PORT}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --timeout 120
}

run_worker() {
  local backoff="${WORKER_RESTART_BACKOFF:-5}"
  echo "[worker] Auto-restart loop (backoff ${backoff}s)"
  while true; do
    set +e
    python buckduit_ai_core.py
    status=$?
    set -e
    echo "[worker] Exited with ${status}. Restarting in ${backoff}s…"
    sleep "${backoff}"
  done
}

case "${cmd}" in
  build)  build ;;
  web)    run_web ;;
  worker) run_worker ;;
  *) echo "Usage: $0 {build|web|worker}" && exit 64 ;;
esac
