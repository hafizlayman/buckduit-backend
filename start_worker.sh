#!/usr/bin/env bash
set -e

echo "▶️  Starting BuckDuit worker..."
python -m workers.auto_sync_worker
