import os, time, requests

# Render sets RENDER_EXTERNAL_URL for web services. Fallback to local.
base = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
if not base:
    port = os.getenv("PORT", "5000")
    base = f"http://127.0.0.1:{port}"

HEALTH_URL = f"{base}/health"
INTERVAL_SEC = int(os.getenv("PING_INTERVAL_SEC", "600"))  # 10 minutes

def ping():
    try:
        r = requests.get(HEALTH_URL, timeout=10)
        print(f"[pinger] {HEALTH_URL} -> {r.status_code}")
    except Exception as e:
        print(f"[pinger] error: {e}")

if __name__ == "__main__":
    print(f"[pinger] starting; target={HEALTH_URL}, every {INTERVAL_SEC}s")
    while True:
        ping()
        time.sleep(INTERVAL_SEC)
