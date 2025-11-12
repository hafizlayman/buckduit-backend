# backend/services/ai_sentiment.py
from __future__ import annotations
import hashlib
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List

def _seed_from_date(dt: datetime) -> float:
    """Deterministic pseudo-random seed from date so values are stable per-day."""
    h = hashlib.sha256(dt.strftime("%Y-%m-%d").encode()).hexdigest()
    # Map hex to 0..1
    return int(h[:8], 16) / 0xFFFFFFFF

def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def get_ai_sentiment(now: datetime | None = None) -> Dict:
    """
    Returns overall AI 'mood' for the system: score (-1..1), label, confidence 0..1.
    This version is deterministic by date (no DB dependency) so it runs everywhere.
    """
    now = now or datetime.now(timezone.utc)
    seed = _seed_from_date(now)

    # Smooth daily curve between -0.35..+0.35, then nudge with seed
    base = math.sin(now.timetuple().tm_yday / 365 * 2 * math.pi) * 0.35
    score = max(-1.0, min(1.0, base + (seed - 0.5) * 0.6))  # clamp

    if score > 0.15:
        label = "Bullish"
    elif score < -0.15:
        label = "Bearish"
    else:
        label = "Neutral"

    # Confidence: higher when |score| is larger
    confidence = round(min(0.95, 0.55 + abs(score) * 0.4), 2)

    reason = (
        "Model outlook derived from anomaly rate, auto-heal frequency, and threshold stability. "
        "This demo build uses a deterministic daily generator (no DB dependency)."
    )

    return {
        "timestamp": now.isoformat(),
        "score": round(score, 3),
        "label": label,
        "confidence": confidence,
        "reason": reason,
    }

def get_risk_flow(days: int = 7, now: datetime | None = None) -> Dict[str, List[Dict]]:
    """
    Returns a time series of daily high/medium/low risk counts for the last `days`.
    Deterministic by date — safe to show when DB is empty.
    """
    now = now or datetime.now(timezone.utc)
    start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    series: List[Dict] = []
    for i in range(days):
        d = start + timedelta(days=i)
        s = _seed_from_date(d)

        # Shape counts to look realistic but stable
        base_low = int(_lerp(5, 10, s))
        base_med = int(_lerp(2, 5, (s * 1.7) % 1))
        base_high = int(_lerp(0, 3, (s * 2.3) % 1))

        # Slight weekly wave
        weekly = math.sin((d.weekday() / 6) * math.pi)  # 0..pi
        base_med = max(0, base_med + (1 if weekly > 0.8 else 0))
        base_high = max(0, base_high + (1 if weekly > 0.9 else 0))

        series.append({
            "date": d.date().isoformat(),
            "low": base_low,
            "medium": base_med,
            "high": base_high,
        })

    return {"items": series}
