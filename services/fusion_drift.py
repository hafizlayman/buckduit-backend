# ======================================================
# Fusion Drift Engine — Stage 13.92 (Fusion Drift v1)
# ======================================================

from datetime import datetime
from statistics import mean
from ai.ai_fusion_memory import get_fusion_memory  # ✅ FIXED IMPORT PATH


def compute_fusion_drift(window: int = 10):
    """
    Compute fusion drift based on historical fusion memory data.
    Uses moving average and delta change detection.
    """
    memory_data = get_fusion_memory() or []

    if not memory_data:
        return {
            "drift_index": 0.0,
            "velocity": 0.0,
            "stability": 1.0,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "No fusion memory data available."
        }

    # Sort chronologically by timestamp
    memory_data = sorted(memory_data, key=lambda x: x.get("timestamp", ""))[-window:]

    fusion_values = [float(i.get("fusion", 0)) for i in memory_data]
    confidence_values = [float(i.get("confidence", 0)) for i in memory_data]

    if len(fusion_values) < 2:
        return {
            "drift_index": 0.0,
            "velocity": 0.0,
            "stability": 1.0,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Insufficient data for drift analysis."
        }

    # Compute drift velocity (change rate)
    diffs = [fusion_values[i] - fusion_values[i - 1] for i in range(1, len(fusion_values))]
    velocity = mean(diffs)

    # Stability = inverse of absolute drift velocity
    stability = max(0.0, 1 - abs(velocity))

    # Drift index combines both velocity and confidence
    drift_index = round(mean(confidence_values) * (1 - stability), 4)

    result = {
        "drift_index": drift_index,
        "velocity": round(velocity, 4),
        "stability": round(stability, 4),
        "timestamp": datetime.utcnow().isoformat(),
        "note": "Fusion drift computed successfully."
    }

    return result
