# backend/services/live_drift_service.py
# Stage 14.06 — Live Drift Smoother + Bias Guardrails (service layer)

from __future__ import annotations
import math, random
from datetime import datetime, timedelta, timezone

def _seed_noise(seed_shift: int = 0) -> float:
    # Lightweight deterministic-ish noise so charts look alive but stable
    base = math.sin(datetime.now(timezone.utc).timestamp() / 300.0 + seed_shift)
    return base * 0.05 + (random.random() - 0.5) * 0.02

def _ema(values, alpha: float):
    if not values:
        return []
    smoothed = [values[0]]
    for v in values[1:]:
        smoothed.append(alpha * v + (1 - alpha) * smoothed[-1])
    return smoothed

def generate_live_drift(minutes: int = 180, step: int = 5, alpha: float = 0.35):
    """
    Generate a recent time series:
      - 'actual_drift' (simulated ground truth drift)
      - 'predicted_drift' (model output + small noise)
      - 'smoothed_drift' (EMA over predicted)
      - 'bias' = smoothed - actual
    """
    points = max(8, minutes // step)  # at least 8 points
    now = datetime.now(timezone.utc)
    times = [now - timedelta(minutes=step * i) for i in reversed(range(points))]

    # Simulate a slowly-varying drift (seasonal-ish)
    actual = []
    for idx, t in enumerate(times):
        base = 0.12 * math.sin(idx / 6.0)  # in range ~[-0.12, 0.12]
        drift = base + _seed_noise(1)
        actual.append(drift)

    predicted = []
    for idx, v in enumerate(actual):
        # add modest estimation error, small lag + noise
        err = 0.02 * math.sin(idx / 5.0) + _seed_noise(2)
        predicted.append(v + err)

    smoothed = _ema(predicted, alpha=alpha)
    bias = [s - a for s, a in zip(smoothed, actual)]

    data = []
    for t, a, p, s, b in zip(times, actual, predicted, smoothed, bias):
        data.append({
            "time": t.isoformat(),
            "actual_drift": round(a, 6),
            "predicted_drift": round(p, 6),
            "smoothed_drift": round(s, 6),
            "bias": round(b, 6),
        })
    return data

def summarize_bias(rows, threshold: float = 0.12):
    if not rows:
        return {
            "ok": True,
            "flagged": False,
            "bias_mean": 0.0,
            "bias_abs_max": 0.0,
            "reasons": ["empty series"],
        }
    biases = [r["bias"] for r in rows]
    mean = sum(biases) / len(biases)
    abs_max = max(abs(b) for b in biases)

    flagged = abs_max > threshold or abs(mean) > (threshold * 0.7)
    reasons = []
    if abs_max > threshold:
        reasons.append(f"abs_max({abs_max:.3f}) > threshold({threshold:.3f})")
    if abs(mean) > (threshold * 0.7):
        reasons.append(f"abs_mean({abs(mean):.3f}) > 0.7 * threshold")

    return {
        "ok": True,
        "flagged": flagged,
        "bias_mean": round(mean, 6),
        "bias_abs_max": round(abs_max, 6),
        "threshold": threshold,
        "reasons": reasons or ["within guardrails"],
    }
