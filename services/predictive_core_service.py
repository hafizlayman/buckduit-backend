# =========================================
# backend/services/predictive_core_service.py
# Stage 13.94 — Runtime-aware Predictive Core
# =========================================
from __future__ import annotations
import os, random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from config.ai_runtime import get_params   # ✅ NEW — read live tuner params


# ---------- Supabase client helper ----------
def _maybe_supabase():
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None


# ---------- Synthetic fallback ----------
def _synthetic_rows(n: int = 120) -> List[Dict[str, Any]]:
    severities = ["low", "medium", "high", "critical"]
    categories = ["api", "worker", "db", "auth", "cache", "router"]
    base = datetime.utcnow()
    rows: List[Dict[str, Any]] = []

    for i in range(n):
        ts = base - timedelta(minutes=i * 5)
        sev = random.choices(severities, weights=[50, 30, 15, 5], k=1)[0]
        risk_map = {
            "low": random.uniform(0.02, 0.12),
            "medium": random.uniform(0.10, 0.30),
            "high": random.uniform(0.28, 0.55),
            "critical": random.uniform(0.50, 0.95),
        }
        risk = risk_map[sev]
        rows.append({
            "id": i + 1,
            "created_at": ts.isoformat() + "Z",
            "severity": sev,
            "category": random.choice(categories),
            "ai_confidence": round(risk, 4),
            "message": f"synthetic event {i} ({sev})",
        })
    return rows


# ---------- Fetch data ----------
def fetch_recent_rows(limit: int = 200) -> List[Dict[str, Any]]:
    sb = _maybe_supabase()
    if sb is None:
        return _synthetic_rows(min(limit, 400))
    try:
        resp = (
            sb.table("system_logs")
            .select("id,created_at,severity,category,ai_confidence,message")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception:
        return _synthetic_rows(min(limit, 400))


# ---------- Math helpers ----------
def _pct(n: int, d: int) -> float:
    return round((n / d) * 100.0, 2) if d else 0.0

def _avg(xs: List[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


# ---------- Predictive summary ----------
def compute_predictive_summary(rows: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """
    rows is optional. If None, fetches DB (or synthetic).
    Uses live runtime params from adaptive tuner registry.
    """
    # ✅ Grab live adaptive tuner parameters
    params = get_params()
    lr = params.get("learning_rate", 0.05)
    cw = params.get("correction_weight", 0.5)

    if rows is None:
        rows = fetch_recent_rows(200)

    total = len(rows)
    severities = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    risks: List[float] = []

    for r in rows:
        sev = str(r.get("severity", "low")).lower()
        if sev not in severities:
            sev = "low"
        severities[sev] += 1
        try:
            risks.append(float(r.get("ai_confidence", 0.0)))
        except Exception:
            pass

    avg_risk = _avg(risks)

    # ✅ Integrate learning-rate scaling into drift math
    if total >= 20:
        q = max(1, total // 4)
        head = risks[:q]
        tail = risks[-q:]
        drift = round((_avg(head) - _avg(tail)) * (1 + lr * cw), 4)
    else:
        drift = 0.0

    risk_score = round(min(max(avg_risk * 100.0, 1.0), 99.0), 2)

    return {
        "total_events": total,
        "severity_breakdown": severities,
        "average_risk": round(avg_risk, 4),
        "drift_vs_past_quarter": drift,
        "risk_score": risk_score,
        "runtime_params": params,     # ✅ shows what tuning was applied
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
