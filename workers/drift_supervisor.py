# backend/workers/drift_supervisor.py
# Stage 14.15 — supervisor loop that forecasts drift and notifies Telegram

import os, time, json, threading
import requests
from typing import Optional, Dict, Any
from services.drift_forecast import compute_drift

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
SERVICE_NAME = os.getenv("SERVICE_NAME", "buckduit-backend")
HEALTH_URL = os.getenv("HEALTH_URL", "http://127.0.0.1:5000/health")
DRIFT_INTERVAL_SEC = int(os.getenv("DRIFT_INTERVAL_SEC", "90") or 90)

_last_state: Dict[str, Any] = {"alert_sent": False, "warn_sent": False}

def _tg_send(text: str) -> None:
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
        requests.post(url, json=payload, timeout=12)
    except Exception:
        pass


def _health_ok() -> bool:
    try:
        r = requests.get(HEALTH_URL, timeout=6)
        return r.ok
    except Exception:
        return False


def run_once() -> Dict[str, Any]:
    drift = compute_drift()
    flags = drift.get("flags", {})
    alert = bool(flags.get("alert"))
    warn = bool(flags.get("warn"))

    # State-machine to avoid spamming
    if alert and not _last_state.get("alert_sent"):
        _tg_send(f"🚨 [{SERVICE_NAME}] DRIFT ALERT — z={drift['last']['zscore']:.2f} (src: {drift['source']})")
        _last_state["alert_sent"] = True
        _last_state["warn_sent"] = True  # implied
    elif (not alert) and _last_state.get("alert_sent"):
        _tg_send(f"✅ [{SERVICE_NAME}] Drift stabilized — back under alert threshold.")
        _last_state["alert_sent"] = False

    if warn and not _last_state.get("warn_sent") and not alert:
        _tg_send(f"⚠️ [{SERVICE_NAME}] Drift warning — z={drift['last']['zscore']:.2f}")
        _last_state["warn_sent"] = True
    elif (not warn) and _last_state.get("warn_sent") and not alert:
        _tg_send(f"ℹ️ [{SERVICE_NAME}] Warning cleared.")
        _last_state["warn_sent"] = False

    return {
        "drift": drift,
        "health_ok": _health_ok(),
        "state": dict(_last_state),
    }


def loop_forever():
    while True:
        try:
            run_once()
        except Exception:
            # swallow to keep the worker alive
            pass
        time.sleep(DRIFT_INTERVAL_SEC)


def start_background_thread() -> threading.Thread:
    t = threading.Thread(target=loop_forever, daemon=True)
    t.start()
    return t
