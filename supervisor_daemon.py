# ==========================================================
# BuckDuit Supervisor Daemon — Stage 14.14
# Multi-Process Engine for Flask + Workers
# ==========================================================
import subprocess, time, os, signal, sys

# ==========================================================
# 1️⃣ Define All Managed Processes
# ==========================================================
# Each entry: name → [command list]
processes = {
    "flask_backend": ["python3", "app.py"],  # main Flask app
    "heartbeat_ai": ["python3", "backend/workers/heartbeat_ai.py"],  # optional worker
}

# ==========================================================
# 2️⃣ Helper — Launch Process
# ==========================================================
def launch(name, cmd):
    try:
        print(f"🚀 Launching {name}: {' '.join(cmd)}")
        return subprocess.Popen(cmd, preexec_fn=os.setsid)
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None

# ==========================================================
# 3️⃣ Core Supervisor Loop
# ==========================================================
def monitor():
    running = {}
    for name, cmd in processes.items():
        if os.path.exists(cmd[-1]):
            running[name] = launch(name, cmd)
        else:
            print(f"⚠️ File missing for {name}: {cmd[-1]} (skipped)")

    print("♻️ Supervisor monitoring all processes...")

    while True:
        time.sleep(10)
        for name, proc in list(running.items()):
            if proc.poll() is not None:  # process died
                print(f"⚠️ {name} stopped (exit={proc.poll()}). Restarting in 5s...")
                time.sleep(5)
                running[name] = launch(name, processes[name])

# ==========================================================
# 4️⃣ Graceful Shutdown
# ==========================================================
def shutdown_all(running):
    print("\n🛑 Shutting down all processes...")
    for name, proc in running.items():
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            print(f"✅ {name} terminated")
        except Exception as e:
            print(f"⚠️ Failed to terminate {name}: {e}")

# ==========================================================
# 5️⃣ Entry Point
# ==========================================================
if __name__ == "__main__":
    print("🧠 BuckDuit Supervisor Daemon (Stage 14.14)")
    try:
        monitor()
    except KeyboardInterrupt:
        shutdown_all({})
        sys.exit(0)
