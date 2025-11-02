# auto_healer.py
import os, sys, threading, time
from datetime import datetime, timezone
from typing import Callable
from ai_telemetry import supabase_client, get_last_heartbeat, heartbeat_upsert

HEARTBEAT_SECONDS = int(os.getenv("HEARTBEAT_SECONDS", "60"))
HEAL_MAX_MISSES  = int(os.getenv("HEAL_MAX_MISSES", "3"))    # 3 missed heartbeats => attempt recovery
FORCE_RESTART_AFTER_FAILS = int(os.getenv("FORCE_RESTART_AFTER_FAILS", "2"))  # if soft-recovery fails X times -> exit(1)
NODE_ID = int(os.getenv("AI_CORE_NODE_ID", "1"))

def _parse_dt(s: str):
    # robust ISO parser
    try:
        return datetime.fromisoformat(s.replace("Z","+00:00"))
    except Exception:
        return None

class AutoHealer(threading.Thread):
    """
    Watches the heartbeat row and triggers:
      1) soft_recover() callback (you provide) when stalled
      2) if soft recover fails repeatedly, sys.exit(1) to let Railway auto-restart
    """
    daemon = True

    def __init__(self, soft_recover: Callable[[], bool]):
        super().__init__(name="AutoHealer")
        self._stop = threading.Event()
        self._soft_recover = soft_recover
        self._consecutive_failures = 0

    def stop(self):  # not used yet, but handy
        self._stop.set()

    def run(self):
        sb = supabase_client()
        while not self._stop.is_set():
            try:
                last_hb, _ = get_last_heartbeat(sb, NODE_ID)
                now = datetime.now(timezone.utc)
                stalled = False

                if last_hb:
                    dt = _parse_dt(last_hb)
                    if dt and (now - dt).total_seconds() > HEARTBEAT_SECONDS * HEAL_MAX_MISSES:
                        stalled = True
                else:
                    # never reported yet after boot; give grace period
                    stalled = True if self._consecutive_failures > 0 else False

                if stalled:
                    # mark “degraded”
                    try:
                        heartbeat_upsert(sb, NODE_ID, status="degraded", err="missed heartbeats")
                    except Exception:
                        pass

                    ok = False
                    try:
                        ok = self._soft_recover()
                    except Exception:
                        ok = False

                    if ok:
                        self._consecutive_failures = 0
                    else:
                        self._consecutive_failures += 1

                        if self._consecutive_failures >= FORCE_RESTART_AFTER_FAILS:
                            # Hard fail: exit so Railway auto-restarts the container.
                            try:
                                heartbeat_upsert(sb, NODE_ID, status="exiting", err="auto-heal hard restart")
                            except Exception:
                                pass
                            sys.stderr.write("AutoHealer: hard-restart triggered\n")
                            sys.stderr.flush()
                            time.sleep(1)
                            os._exit(1)  # immediate exit -> Railway restarts per policy

                time.sleep(HEARTBEAT_SECONDS)  # check once per heartbeat window
            except Exception as e:
                # Don’t die — log and continue
                sys.stderr.write(f"AutoHealer loop error: {e}\n")
                sys.stderr.flush()
                time.sleep(HEARTBEAT_SECONDS)
