import os
import subprocess
import time
import datetime
import sys
import requests
from pathlib import Path

# =====================================================
# CONFIG
# =====================================================
LOG_PATH = "error_log.txt"
CORE_FILE = "buckduit_ai_core.py"

# Load .env manually to get Telegram credentials
if Path(".env").exists():
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =====================================================
# HELPER FUNCTIONS
# =====================================================
def log(msg):
    """Write timestamped logs to console and file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    print(line.strip())
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)

def send_telegram_alert(message):
    """Send Telegram message if configured."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        log(f"⚠️ Telegram send failed: {e}")

# =====================================================
# CORE RUNNER
# =====================================================
def run_core():
    """Launch and monitor the AI Core."""
    try:
        log("🚀 Starting BuckDuit AI Core...")
        process = subprocess.Popen(
            [sys.executable, CORE_FILE],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Continuously read output
        while True:
            line = process.stdout.readline()
            if line:
                print(line.strip())
                if "Traceback" in line or "❌" in line:
                    log(f"⚠️ Error detected: {line.strip()}")
            err = process.stderr.readline()
            if err:
                log(f"💀 STDERR: {err.strip()}")

            # Restart if process ends
            if process.poll() is not None:
                code = process.returncode
                log(f"❌ Process exited with code {code}. Restarting in 10 seconds...")
                send_telegram_alert("⚠️ <b>BuckDuit AI Core crashed</b>. Restarting in 10 seconds.")
                time.sleep(10)
                return  # trigger restart
    except Exception as e:
        log(f"🔥 Supervisor caught exception: {e}")
        send_telegram_alert(f"🔥 <b>Supervisor exception</b>: {e}")
        time.sleep(10)

# =====================================================
# SUPERVISOR MAIN LOOP
# =====================================================
def main():
    """Keep the AI Core alive forever."""
    send_telegram_alert("🧠 BuckDuit Supervisor started (monitoring AI Core).")
    while True:
        run_core()
        log("♻️ Restarting AI Core loop...")
        time.sleep(5)

if __name__ == "__main__":
    log("🧠 BuckDuit Supervisor initialized.")
    main()
