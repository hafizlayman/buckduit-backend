# backend/services/predictive_service.py
import random
from datetime import datetime


def run_predictive_analysis(data):
    """
    Simulated predictive analysis function.
    Accepts incoming JSON data and returns a mock AI prediction.
    Replace with real model logic later.
    """

    try:
        # Extract any relevant parameters (safe default)
        input_features = data or {}

        # Simulate prediction outputs
        ai_score = round(random.uniform(0.6, 0.98), 3)
        drift_value = round(random.uniform(-0.5, 0.5), 2)
        trend = "stable" if abs(drift_value) < 0.25 else "drifting"

        # Mock risk calculation
        risk_level = (
            "low" if ai_score > 0.8 else
            "medium" if ai_score > 0.6 else
            "high"
        )

        # Create timestamp
        timestamp = datetime.utcnow().isoformat()

        # Return structured response
        return {
            "timestamp": timestamp,
            "ai_score": ai_score,
            "drift": drift_value,
            "trend": trend,
            "risk_level": risk_level,
            "input_data": input_features
        }

    except Exception as e:
        print(f"[Predictive Service] ❌ Error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
# --- Predictive Risk helpers (append) ---
from statistics import mean, pstdev
from datetime import datetime, timedelta

def _ema(values, span=7):
    if not values: 
        return None
    alpha = 2 / (span + 1)
    ema = values[0]
    for v in values[1:]:
        ema = alpha * v + (1 - alpha) * ema
    return ema

def compute_predictive_summary(rows, baseline_days=7, z_alert=1.8, min_points=12):
    """
    rows: list[dict] with 'timestamp' (iso) and 'ai_score' (float) and optional 'drift'
    returns dict for RiskSummaryCard
    """
    pts = []
    for r in rows:
        try:
            s = float(r.get("ai_score"))
            pts.append(s)
        except Exception:
            continue

    latest_score = pts[-1] if pts else None
    n = len(pts)

    if n < max(3, min_points):
        return {
            "ok": False,
            "reason": f"insufficient_points:{n}",
            "latest_score": latest_score,
            "n": n
        }

    ema_baseline = _ema(pts, span=baseline_days) or mean(pts)
    # population std to be stable on rolling streams
    sigma = pstdev(pts) if n > 1 else 0.0
    z = 0.0 if sigma == 0 else (latest_score - ema_baseline) / sigma

    risk_level = "low"
    if abs(z) >= z_alert:
        risk_level = "high"
    elif abs(z) >= z_alert * 0.6:
        risk_level = "moderate"

    trend = "flat"
    if n >= 3 and pts[-1] > pts[-2] > pts[-3]:
        trend = "up"
    elif n >= 3 and pts[-1] < pts[-2] < pts[-3]:
        trend = "down"

    return {
        "ok": True,
        "n": n,
        "latest_score": latest_score,
        "ema": ema_baseline,
        "sigma": sigma,
        "zscore": z,
        "risk": risk_level,
        "trend": trend,
        "asof": datetime.utcnow().isoformat()
    }

def build_anomaly_heatmap(rows, days=7):
    """
    Compress last N days of points into a 7x24 (day x hour) heatmap (or fewer cols if less data).
    Cell = z-score bucket (-2..+2 clipped). Frontend will render as small grid.
    """
    # bucket by day-hour
    from collections import defaultdict
    buckets = defaultdict(list)
    cutoff = datetime.utcnow() - timedelta(days=days)
    series = []

    for r in rows:
        try:
            ts = r.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
            if ts < cutoff:
                continue
            s = float(r.get("ai_score"))
            series.append((ts, s))
        except Exception:
            continue

    if not series:
        return {"days": [], "grid": []}

    series.sort(key=lambda x: x[0])
    vals = [v for _, v in series]
    mu = mean(vals)
    sd = pstdev(vals) if len(vals) > 1 else 1.0

    for ts, v in series:
        dkey = ts.strftime("%Y-%m-%d")
        h = ts.hour
        z = 0 if sd == 0 else (v - mu) / sd
        # clip to -2..2 for color range
        z = max(-2.0, min(2.0, z))
        buckets[(dkey, h)].append(z)

    # assemble day labels (newest last)
    unique_days = sorted({d for (d, _) in buckets.keys()})
    # build grid rows per day; 24 cols
    grid = []
    for d in unique_days:
        row = []
        for h in range(24):
            zs = buckets.get((d, h))
            cell = None if not zs else sum(zs)/len(zs)
            row.append(cell)  # may be None -> “no data”
        grid.append(row)

    return {"days": unique_days, "grid": grid}
