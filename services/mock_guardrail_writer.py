# backend/services/mock_guardrail_writer.py
import os, time, random, datetime as dt
from threading import Thread, Event
from supabase import create_client
from utils.ai_logger import log_event
from services.notifier import notify_telegram

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

INTERVAL_SEC     = int(os.getenv("ALERT_POLL_SECONDS", "120"))
BIAS_LIMIT       = float(os.getenv("ALERT_MAX_BIAS", "0.18"))
THRESHOLD        = float(os.getenv("ALERT_BASE_THRESHOLD", "0.12"))
SPIKE_PROB       = float(os.getenv("ALERT_PROB_SPIKE", "0.30"))

_client = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        log_event("INFO", "mock_feeder", "Supabase connected")
except Exception as e:
    log_event("ERROR", "mock_feeder", f"Supabase connect failed: {e}")

stop_ev = Event()

def _insert_alert(message: str, bias_max: float, threshold: float, flagged: bool):
    if not _client:
        log_event("INFO", "mock_feeder", f"[MOCK] alert → {message} | bias={bias_max:.3f} thr={threshold:.3f} flagged={flagged}")
        return
    try:
        _client.table("predictive_alerts").insert({
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "message": message,
            "bias_max": round(bias_max, 6),
            "threshold": round(threshold, 6),
            "flagged": flagged
        }).execute()
        log_event("INFO", "mock_feeder", f"alert inserted (flagged={flagged})", {"bias_max": bias_max, "threshold": threshold})
    except Exception as e:
        log_event("ERROR", "mock_feeder", f"insert failed: {e}")

def _make_sample() -> tuple[str, float, float, bool]:
    # baseline wandering bias (small), occasional spike
    base = random.uniform(-0.08, 0.08)
    spike = 0.0
    if random.random() < SPIKE_PROB:
        spike = random.uniform(THRESHOLD * 1.05, BIAS_LIMIT * 1.1) * random.choice([-1.0, 1.0])
    bias = base + spike
    bias_abs = abs(bias)

    flagged = bias_abs >= THRESHOLD
    if flagged:
        msg = f"Guardrail breach: |bias|={bias_abs:.3f} ≥ thr={THRESHOLD:.3f}"
    else:
        msg = f"Within guardrails: |bias|={bias_abs:.3f} < thr={THRESHOLD:.3f}"
    return msg, bias_abs, THRESHOLD, flagged

def _loop():
    log_event("INFO", "mock_feeder", f"started (interval={INTERVAL_SEC}s, thr={THRESHOLD})")
    while not stop_ev.is_set():
        try:
            # generate 1–3 samples each cycle
            for _ in range(random.randint(1, 3)):
                msg, bias_abs, thr, flagged = _make_sample()
                _insert_alert(msg, bias_abs, thr, flagged)
                # optional notify if flagged
                if flagged:
                    notify_telegram(f"🚨 BuckDuit Guardrail\n<bias_abs> {bias_abs:.3f}\n<threshold> {thr:.3f}\n{msg}")
                time.sleep(1.0)
        except Exception as e:
            log_event("ERROR", "mock_feeder", f"loop error: {e}")
        finally:
            stop_ev.wait(INTERVAL_SEC)
    log_event("INFO", "mock_feeder", "stopped")

_thread: Thread | None = None

def start_mock_guardrail_writer():
    global _thread
    if _thread and _thread.is_alive():
        return
    _thread = Thread(target=_loop, name="mock_guardrail_writer", daemon=True)
    _thread.start()
    log_event("INFO", "app_boot", "mock guardrail writer started")

def stop_mock_guardrail_writer():
    stop_ev.set()
