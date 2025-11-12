import os, time
from datetime import datetime
from monitor.predictive_failure_ai import run_batch

INTERVAL_SEC = int(os.getenv("PRED_WORKER_INTERVAL_SEC", "900"))  # default 15m
HORIZON = int(os.getenv("PRED_DEFAULT_HORIZON_MIN", "60"))

def main():
    print(f"[predictive_worker] starting interval={INTERVAL_SEC}s horizon={HORIZON}m")
    while True:
        try:
            out = run_batch(horizon_min=HORIZON)
            print(f"[predictive_worker] {datetime.utcnow().isoformat()} wrote {len(out)} forecasts")
        except Exception as e:
            print(f"[predictive_worker] error: {e}")
        time.sleep(INTERVAL_SEC)

if __name__ == "__main__":
    main()
    