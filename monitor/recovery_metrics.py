import os
import json
from datetime import datetime

# === Recovery Metrics Path ===
METRICS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "recovery_metrics.json")
os.makedirs(os.path.dirname(METRICS_PATH), exist_ok=True)

def get_recovery_metrics():
    """
    Reads and returns current recovery metrics from local cache.
    If missing, returns default baseline metrics.
    """
    try:
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, "r") as f:
                data = json.load(f)
        else:
            data = {
                "avg_recovery_time": 0,
                "total_recoveries": 0,
                "last_recovery": None,
            }
        return data

    except Exception as e:
        print(f"⚠️ Error reading recovery metrics: {e}")
        return {
            "avg_recovery_time": 0,
            "total_recoveries": 0,
            "last_recovery": None,
        }

def record_recovery(duration: float):
    """
    Updates local metrics file when a new recovery is performed.
    """
    try:
        current = get_recovery_metrics()

        total = current.get("total_recoveries", 0) + 1
        avg_time = (
            (current.get("avg_recovery_time", 0) * (total - 1) + duration) / total
        )

        updated = {
            "avg_recovery_time": round(avg_time, 2),
            "total_recoveries": total,
            "last_recovery": datetime.utcnow().isoformat(),
        }

        with open(METRICS_PATH, "w") as f:
            json.dump(updated, f, indent=2)

        print(f"✅ Recovery metrics updated: {updated}")

    except Exception as e:
        print(f"⚠️ Failed to update recovery metrics: {e}")
