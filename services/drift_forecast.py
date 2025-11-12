# backend/services/drift_forecast.py
# Stage 14.15 — Drift Forecast Core (Supabase-optional, mock-safe)

import os, time, statistics as stats
from typing import Dict, Any, List, Optional

# ---- Optional Supabase (safe if missing) ----
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
SUPABASE_TABLE = os.getenv("DRIFT_SOURCE_TABLE", "sync_status")

_supabase = None
def _get_supabase():
    global _supabase
    if _supabase is not None:
        return _supabase
    if not (SUPABASE_URL and SUPABASE_SERVICE_KEY):
        return None
    try:
        from supabase import create_client, Client
        _supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)  # type: ignore
        return _supabase
    except Exception:
        return None


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "").strip() or default)
    except Exception:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except Exception:
        return default


# ---- Tunables (with sane defaults) ----
DRIFT_LOOKBACK = _env_int("DRIFT_LOOKBACK", 100)           # sample count to read
DRIFT_WINDOW = _env_int("DRIFT_WINDOW", 20)                # moving window for mean/std
DRIFT_Z_THRESHOLD = _env_float("DRIFT_Z_THRESHOLD", 2.5)   # alert when |z| >= threshold
DRIFT_WARN_Z = _env_float("DRIFT_WARN_Z", 1.8)             # soft warn band


def _fetch_series_from_supabase(column: str = "latency_ms") -> List[float]:
    """
    Reads a numeric series from Supabase table (newest first).
    Expects rows with 'created_at' and numeric 'column'.
    Returns a list oldest -> newest.
    """
    client = _get_supabase()
    if not client:
        return []

    try:
        # newest first (limit)
        resp = (
            client.table(SUPABASE_TABLE)
            .select(f"{column},created_at")
            .order("created_at", desc=True)
            .limit(DRIFT_LOOKBACK)
            .execute()
        )
        rows = resp.data or []
        series = []
        for r in rows:
            v = r.get(column)
            if v is None:
                continue
            try:
                series.append(float(v))
            except Exception:
                continue
        series.reverse()  # oldest -> newest
        return series
    except Exception:
        return []


def _mock_series() -> List[float]:
    """Fallback series if Supabase is not configured."""
    import random
    base = 100.0
    s: List[float] = []
    for i in range(DRIFT_LOOKBACK):
        jitter = random.uniform(-3, 3)
        # last 15 points slightly drift up
        drift = (i - (DRIFT_LOOKBACK - 15)) * 0.9 if i > DRIFT_LOOKBACK - 15 else 0.0
        s.append(base + jitter + max(0.0, drift))
    return s


def moving_mean_std(values: List[float], window: int) -> List[Dict[str, float]]:
    out: List[Dict[str, float]] = []
    if window < 2:
        window = 2
    for i in range(len(values)):
        lo = max(0, i - window + 1)
        win = values[lo:i+1]
        m = stats.fmean(win) if win else 0.0
        sd = stats.pstdev(win) if len(win) > 1 else 0.0
        out.append({"mean": m, "std": sd})
    return out


def compute_drift(series: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Returns:
      {
        "points": [...],               # raw series
        "window_stats": [{"mean":..,"std":..}, ...],
        "last": {"value":..,"zscore":..},
        "flags": {"warn":bool,"alert":bool},
        "thresholds": {"warn": float, "alert": float}
      }
    """
    if series is None:
        series = _fetch_series_from_supabase() or _mock_series()

    if not series:
        return {
            "points": [],
            "window_stats": [],
            "last": {"value": None, "zscore": None},
            "flags": {"warn": False, "alert": False},
            "thresholds": {"warn": DRIFT_WARN_Z, "alert": DRIFT_Z_THRESHOLD},
            "msg": "No data",
        }

    wstats = moving_mean_std(series, DRIFT_WINDOW)
    last_v = series[-1]
    last_m = wstats[-1]["mean"]
    last_sd = wstats[-1]["std"]
    z = 0.0
    if last_sd > 1e-9:
        z = (last_v - last_m) / last_sd

    warn = abs(z) >= DRIFT_WARN_Z
    alert = abs(z) >= DRIFT_Z_THRESHOLD

    return {
        "points": series,
        "window_stats": wstats,
        "last": {"value": last_v, "zscore": z, "mean": last_m, "std": last_sd},
        "flags": {"warn": warn, "alert": alert},
        "thresholds": {"warn": DRIFT_WARN_Z, "alert": DRIFT_Z_THRESHOLD},
        "lookback": DRIFT_LOOKBACK,
        "window": DRIFT_WINDOW,
        "source": "supabase" if _get_supabase() else "mock",
        "table": SUPABASE_TABLE,
    }
