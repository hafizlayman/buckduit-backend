import time
import random
from datetime import datetime

# === Adaptive Monitor Simulation ===
def run_adaptive_monitor():
    """
    Simulates adaptive AI monitoring for BuckDuit Core.
    Runs continuously, updating system 'vitals' and trend metrics.
    """
    print("🧩 Adaptive Monitor started successfully.")

    while True:
        try:
            # Simulate random CPU/AI load (mock telemetry)
            cpu_load = round(random.uniform(0.3, 0.9), 2)
            ai_load = round(random.uniform(0.2, 0.95), 2)
            trend_index = round(random.uniform(-0.5, 1.5), 2)

            print(
                f"📊 [AdaptiveMonitor] CPU={cpu_load} | AI Load={ai_load} | Trend={trend_index} | Time={datetime.utcnow().isoformat()}"
            )

            # Sleep between monitoring cycles (every 10 seconds)
            time.sleep(10)

        except Exception as e:
            print(f"⚠️ AdaptiveMonitor error: {e}")
            time.sleep(5)
