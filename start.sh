#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$ROOT_DIR"

echo "🟢 start.sh: mode=${1:-web}"

# pick env file for local; cloud will inject env vars
if [[ -n "${APP_ENV:-}" ]]; then
  case "${APP_ENV,,}" in
    prod|production) ENV_FILE=".env.prod" ;;
    stage|staging)   ENV_FILE=".env.stage" ;;
    dev|development) ENV_FILE=".env.dev" ;;
    *)               ENV_FILE=".env" ;;
  esac
else
  for f in .env.prod .env.stage .env.dev .env; do
    if [[ -f "$f" ]]; then ENV_FILE="$f"; break; fi
  done
fi
echo "🗂  using env file ${ENV_FILE:-<none>}"
if [[ -n "${ENV_FILE:-}" && -f "$ENV_FILE" ]]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs -I{} echo {})
fi

export PORT="${PORT:-5000}"
export FLASK_ENV="${FLASK_ENV:-production}"

case "${1:-web}" in
  web)
    echo "🚀 API on :${PORT}"
    exec gunicorn -w 2 -k gthread -t 120 --graceful-timeout 30 \
      --bind 0.0.0.0:"${PORT}" app:app
    ;;
  worker)
    echo "🛠  Worker bundle"
    exec python services/workers/test_env_loader.py
    ;;
  *)
    echo "❌ Use: web | worker"
    exit 1
    ;;
esac
