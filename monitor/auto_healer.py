# backend/monitor/auto_healer.py
import os, json, time, random, threading, queue
from datetime import datetime, timezone
import requests

def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()

class AutoHealer:
    """
    Generic auto-healer with:
      - in-memory retry queue
      - exponential backoff + jitter
      - lightweight health logging to data/health_status.json
      - optional Supabase connectivity ping (HEAD)
    Use: healer = AutoHealer(name="AdaptiveMonitor", cb_send=send_telegram_message)
    """
    def __init__(self, name: str, cb_send, max_queue=1000):
        self.name = name
        self.cb_send = cb_send  # callback signature: cb_send(message=str)
        self.q = queue.Queue(max_queue)
        self.running = True

        # status file (local)
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.health_path = os.path.join(self.data_dir, "health_status.json")

        # supabase (optional ping)
        self.supabase_url = os.getenv("SUPABASE_URL")

        self._write_status("online", "auto-healer initialized")
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

    # ---------- public API ----------
    def send(self, message: str):
        """Try to send now; enqueue on failure."""
        try:
            self.cb_send(message=message)
            self._write_status("online", "send ok")
        except Exception as e:
            self._write_status("degraded", f"send failed: {e}")
            self._enqueue({"message": message, "attempts": 0, "next_retry_at": time.time() + 2})

    def on_error(self, err: Exception, context: str = ""):
        """Record error + try a quick connectivity check."""
        note = f"{type(err).__name__}: {err}"
        if context:
            note = f"[{context}] {note}"
        self._write_status("error", note)

    def stop(self):
        self.running = False

    # ---------- internals ----------
    def _enqueue(self, item: dict):
        try:
            self.q.put_nowait(item)
        except queue.Full:
            self._write_status("error", "retry queue full; dropping oldest")
            try:
                _ = self.q.get_nowait()
                self.q.put_nowait(item)
            except Exception:
                pass

    def _backoff_seconds(self, attempts: int) -> float:
        # 2, 4, 8, 16, 32, cap ~60 + jitter
        base = min(2 ** max(1, attempts + 1), 60)
        jitter = random.uniform(0.0, 0.3) * base
        return base + jitter

    def _worker_loop(self):
        while self.running:
            try:
                item = self.q.get(timeout=1.0)
            except queue.Empty:
                # periodic background ping (keeps status fresh)
                self._maybe_ping()
                continue

            now = time.time()
            if now < item.get("next_retry_at", 0):
                # not yet – put back and sleep a bit
                self.q.put(item)
                time.sleep(0.5)
                continue

            attempts = item.get("attempts", 0)
            try:
                self.cb_send(message=item["message"])
                self._write_status("online", f"retry success after {attempts} attempts")
            except Exception as e:
                attempts += 1
                wait = self._backoff_seconds(attempts)
                item.update({"attempts": attempts, "next_retry_at": time.time() + wait})
                self._write_status("degraded", f"retry failed (attempt {attempts}): {e}; next in {wait:.1f}s")
                # requeue
                self._enqueue(item)

    def _maybe_ping(self):
        # ping ~ every 15s when idle
        if getattr(self, "_last_ping", 0) + 15 > time.time():
            return
        self._last_ping = time.time()
        if not self.supabase_url:
            return
        try:
            # small HEAD is enough and cheap
            requests.head(self.supabase_url, timeout=3)
            # don’t spam status file on successes
        except Exception as e:
            self._write_status("degraded", f"supabase ping fail: {e}")

    def _write_status(self, status: str, message: str):
        payload = {
            "service": self.name,
            "status": status,         # online | degraded | error
            "message": message,
            "ts": utc_now_iso(),
        }
        try:
            # append-friendly log
            if os.path.exists(self.health_path):
                with open(self.health_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []
            data.append(payload)
            # keep last 500 entries max
            data = data[-500:]
            with open(self.health_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            # never crash the app for logging issues
            pass
