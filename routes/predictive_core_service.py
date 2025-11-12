# backend/services/predictive_core_service.py
from __future__ import annotations
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

def _maybe_supabase():
    try:
        from supabase import create_client  # type: ignore
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None

def _synthetic_rows(n: int = 120) -> List[Dict[str, Any]]:
    severities = ["low", "medium", "high", "critical"]
    categories = ["api", "worker", "db", "auth", "cache", "router"]
    base = datetime.utcnow()
    rows: List[Dict[str, Any]] = []
    for i in range(n):
        ts = base - timedelta(minutes=i * 5)
        sev = random.choices(severities, weights=[50, 30, 15, 5], k=1)[0]
        risk = {
            "low": random.uniform(0.02, 0.12),
            "medium": random.uniform(0.10, 0.30),
            "high": random.uniform(0.28, 0.55),
            "critical": random.uniform(0.50, 0.95),
        }[sev]
        rows.append(
            {
                "id": i + 1,
                "created_at": ts.isoformat() + "Z",
                "severity": sev,
                "category": random.choice(categories),
                "ai_confidence": round(risk, 4),
                "message": f"synthetic event {i} ({sev})",
            }
        )
    return rows

def fetch_recent_rows(limit: int = 200) -> List[Dict[str, Any]]:
    sb = _maybe_supabase()
    if sb is None:
        return _synthetic_rows(min(limit, 400))
    try:
        resp = (
            sb.table("system_logs")
            .select("id,created_at,severity,category,ai_confidence:ai_confidence,message")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        data = resp.data or []
        for r in data:
            if "ai_confidence" not in r and "confidence" in r:
                r["ai_confidence"] = r["confidence"]
        return data
    except Exception:
        return _synthetic_rows(min(limit, 400))

def _pct(n: int, d: int) -> float:
    return round((n / d) * 100.0, 2) if d else 0.0

def _avg(xs: List[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0

def compute_predictive_summary(rows: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """
    rows is optional. If None, fetches (DB or synthetic).
    """
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
    if total >= 20:
        q = max(1, total // 4)
        head = risks[:q]
        tail = risks[-q:]
        drift = round((_avg(head) - _avg(tail)), 4)
    else:
        drift = 0.0

    top_recent = sorted(
        rows[: min(total, 25)],
        key=lambda r: float(r.get("ai_confidence", 0.0)),
        reverse=True,
    )[:5]

    categories: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        cat = str(r.get("category", "uncategorized")).lower()
        categories.setdefault(cat, {"count": 0, "avg_conf": 0.0})
        categories[cat]["count"] += 1

    for cat in categories:
        cat_risks = [
            float(r.get("ai_confidence", 0.0))
            for r in rows
            if str(r.get("category", "uncategorized")).lower() == cat
        ]
        categories[cat]["avg_conf"] = _avg(cat_risks)

    risk_score = round(min(max(avg_risk * 100.0, 1.0), 99.0), 2)

    return {
        "total_events": total,
        "severity_breakdown": {
            "low": severities["low"],
            "medium": severities["medium"],
            "high": severities["high"],
            "critical": severities["critical"],
            "low_pct": _pct(severities["low"], total),
            "medium_pct": _pct(severities["medium"], total),
            "high_pct": _pct(severities["high"], total),
            "critical_pct": _pct(severities["critical"], total),
        },
        "average_risk": round(avg_risk, 4),
        "drift_vs_past_quarter": drift,
        "top_recent": [
            {
                "id": tr.get("id"),
                "created_at": tr.get("created_at"),
                "severity": tr.get("severity"),
                "category": tr.get("category"),
                "ai_confidence": tr.get("ai_confidence", 0.0),
                "message": tr.get("message", ""),
            }
            for tr in top_recent
        ],
        "by_category": categories,
        "risk_score": risk_score,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source": "supabase" if _maybe_supabase() else "synthetic",
    }
