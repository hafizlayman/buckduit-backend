# ==========================================================
# backend/services/drift_service.py
# Stage 14.04 — Drift Forecast Smoother (Hampel + EWMA)
# ==========================================================
from __future__ import annotations
from typing import List, Dict, Any
from datetime import timedelta
from statistics import median
from utils.time_utils import utcnow

try:
    from supabase import Client
except Exception:
    Client = None  # type: ignore


# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------
def _hampel_filter(xs: List[float], k: int = 3, t: float = 3.0) -> List[float]:
    """Clip spikes using median + MAD (Hampel filter)."""
    if not xs:
        return xs
    n = len(xs)
    y = xs[:]
    for i in range(n):
        lo = max(0, i - k)
        hi = min(n, i + k + 1)
        window = xs[lo:hi]
        m = median(window)
        mad = median([abs(v - m) for v in window]) or 1e-9
        if abs(xs[i] - m) > t * 1.4826 * mad:
            y[i] = m
    return y


def _ewma(xs: List[float], alpha: float = 0.3) -> List[float]:
    if not xs:
        return xs
    out = [xs[0]]
    a = max(0.01, min(alpha, 0.99))
    for v in xs[1:]:
        out.append(a * v + (1 - a) * out[-1])
    return out


def _diff(xs: List[float]) -> List[float]:
    if len(xs) < 2:
        return [0.0] * len(xs)
    return [0.0] + [xs[i] - xs[i - 1] for i in range(1, len(xs))]


# ----------------------------------------------------------
# Core logic
# ----------------------------------------------------------
def fetch_confidence_series(supabase: Client, days: int = 30) -> List[Dict[str, Any]]:
    """
    Fetch average ai_confidence by day from offers table.
    Degrades gracefully if table or column missing.
    """
    if not supabase:
        return []

    try:
        from_dt = (utcnow() - timedelta(days=days)).isoformat()
        resp = (
            supabase.table("offers")
            .select("created_at, ai_confidence")
            .gte("created_at", from_dt)
            .execute()
        )
        rows = resp.data or []
    except Exception:
        rows = []

    buckets: Dict[str, list] = {}
    for r in rows:
        ts = r.get("created_at")
        val = r.get("ai_confidence")
        if val is None:
            continue
        day = str(ts)[:10]  # YYYY-MM-DD
        buckets.setdefault(day, []).append(float(val))

    days_sorted = sorted(buckets.keys())
    series = []
    for d in days_sorted:
        vals = buckets[d]
        if not vals:
            continue
        series.append({"ts": d, "value": sum(vals) / len(vals)})
    return series


def smooth_and_drift(series: List[Dict[str, Any]], alpha: float = 0.35) -> Dict[str, Any]:
    """
    Apply Hampel smoothing then EWMA, compute drift (first diff).
    """
    if not series:
        return {"raw": [], "smoothed": [], "drift": [], "alpha": alpha}

    xs = [float(p["value"]) for p in series]
    xs = _hampel_filter(xs, k=3, t=3.0)
    sm = _ewma(xs, alpha=alpha)
    df = _diff(sm)

    return {
        "raw": series,
        "smoothed": [{"ts": series[i]["ts"], "value": sm[i]} for i in range(len(sm))],
        "drift": [{"ts": series[i]["ts"], "value": df[i]} for i in range(len(df))],
        "alpha": alpha,
    }


def summarize_drift(drift_points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute summary statistics for drift array.
    """
    if not drift_points:
        return {"avg": 0.0, "last": 0.0, "max_up": 0.0, "max_down": 0.0}

    vals = [float(p["value"]) for p in drift_points]
    return {
        "avg": sum(vals) / len(vals),
        "last": vals[-1],
        "max_up": max(vals),
        "max_down": min(vals),
    }
