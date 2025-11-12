import os, time, math
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_KEY")
sb: Client = create_client(URL, KEY)

INTERVAL = int(os.getenv("FUSE_INTERVAL_SEC", "300"))
LOOKBACK = int(os.getenv("FUSE_LOOKBACK_MIN", "120"))

W_REAL = float(os.getenv("FUSE_REALTIME_WEIGHT", "0.55"))
W_PRED = float(os.getenv("FUSE_PRED_WEIGHT", "0.35"))
W_CTX = float(os.getenv("FUSE_CONTEXT_WEIGHT", "0.10"))
HALF_LIFE = float(os.getenv("FUSE_DECAY_HALFLIFE_MIN", "45"))
THRESH = float(os.getenv("FUSE_ALERT_THRESHOLD", "70"))

# normalize severities -> 0..100
SEV_MAP = {"DEBUG": 10, "INFO": 20, "WARNING": 55, "ERROR": 75, "CRITICAL": 95}

def label(score: float) -> str:
    if score >= 90: return "CRITICAL"
    if score >= 70: return "HIGH"
    if score >= 50: return "MEDIUM"
    return "LOW"

def _decay_factor(minutes_ago: float) -> float:
    # exponential time decay by half-life
    return 0.5 ** (minutes_ago / max(HALF_LIFE, 1.0))

def fetch_realtime_score(service: str, metric: str, since_iso: str) -> float:
    """Aggregate realtime (system_logs + alerts) as a severity-weighted score with decay."""
    logs = sb.table("system_logs").select("timestamp,severity,source,details") \
        .gte("timestamp", since_iso).execute().data or []
    alerts = sb.table("alerts").select("created_at,severity,source,message") \
        .gte("created_at", since_iso).execute().data or []

    now = datetime.now(timezone.utc)
    total = 0.0
    weight = 0.0

    # system_logs
    for r in logs:
        t = r.get("timestamp")
        sev = r.get("severity", "INFO")
        sev_score = SEV_MAP.get(sev, 30)
        if not t: 
            continue
        dt = datetime.fromisoformat(t)
        minutes = (now - dt).total_seconds() / 60.0
        w = _decay_factor(minutes)
        total += sev_score * w
        weight += w

    # alerts
    for r in alerts:
        t = r.get("created_at")
        sev = r.get("severity", "INFO")
        sev_score = SEV_MAP.get(sev, 30)
        if not t:
            continue
        dt = datetime.fromisoformat(t)
        minutes = (now - dt).total_seconds() / 60.0
        w = _decay_factor(minutes)
        total += sev_score * w
        weight += w

    if weight == 0:
        return 0.0
    # bound score 0..100
    return max(0.0, min(100.0, total / weight))

def fetch_predictive(service: str, metric: str, since_iso: str) -> float:
    rows = sb.table("predictive_forecasts").select("risk_score,created_at") \
        .eq("service", service).eq("metric", metric) \
        .gte("created_at", since_iso).order("created_at", desc=True).limit(10) \
        .execute().data or []
    if not rows:
        return 0.0
    # recent highest risk (with slight decay)
    now = datetime.now(timezone.utc)
    best = 0.0
    for r in rows:
        score = float(r["risk_score"])
        dt = datetime.fromisoformat(r["created_at"])
        minutes = (now - dt).total_seconds() / 60.0
        score *= _decay_factor(minutes)  # decay
        best = max(best, score)
    return best

def fetch_context_boost(service: str, metric: str, since_iso: str) -> float:
    """Escalations & heals in lookback window nudge risk."""
    es = sb.table("fused_alert_signals").select("created_at,fused_score") \
        .eq("service", service).eq("metric", metric) \
        .gte("created_at", since_iso).order("created_at", desc=True) \
        .execute().data or []
    # recent high fused -> momentum
    if not es:
        return 0.0
    now = datetime.now(timezone.utc)
    boost = 0.0
    for r in es[:5]:
        sc = float(r["fused_score"])
        dt = datetime.fromisoformat(r["created_at"])
        minutes = (now - dt).total_seconds() / 60.0
        boost += (sc/100.0) * _decay_factor(minutes) * 20.0  # max ~20
    return min(boost, 20.0)

def fuse_once(service: str, metric: str):
    since = (datetime.now(timezone.utc) - timedelta(minutes=LOOKBACK)).isoformat()

    realtime = fetch_realtime_score(service, metric, since)
    predictive = fetch_predictive(service, metric, since)
    context = fetch_context_boost(service, metric, since)

    fused = (W_REAL*realtime) + (W_PRED*predictive) + (W_CTX*context)
    fused = max(0.0, min(100.0, fused))

    components = {
        "realtime": round(realtime,1),
        "predictive": round(predictive,1),
        "recent_escalations": round(context,1),
        "weights": {"real": W_REAL, "pred": W_PRED, "ctx": W_CTX},
        "decay_halflife_min": HALF_LIFE
    }
    row = {
        "service": service,
        "metric": metric,
        "fused_score": round(fused,1),
        "label": label(fused),
        "components": components
    }
    sb.table("fused_alert_signals").insert(row).execute()

    # soft trigger — log into system_logs for visibility (your self-healer can listen)
    if fused >= THRESH:
        try:
            sb.table("system_logs").insert({
                "severity": "WARNING" if fused < 90 else "CRITICAL",
                "source": "AI_FUSION",
                "details": f"Fused risk {row['label']} ({row['fused_score']}) for {service}:{metric}"
            }).execute()
        except Exception:
            pass

    return row

def tracked_pairs() -> list[tuple[str,str]]:
    # unify with predictive worker env
    env = os.getenv("PRED_METRICS", "backend:api_latency_ms,backend:error_rate")
    pairs = []
    for x in env.split(","):
        x = x.strip()
        if not x or ":" not in x: 
            continue
        s,m = x.split(":",1)
        pairs.append((s.strip(), m.strip()))
    return pairs

def main():
    print(f"[fusion_worker] interval={INTERVAL}s lookback={LOOKBACK}m")
    while True:
        try:
            pairs = tracked_pairs()
            out = [fuse_once(s,m) for (s,m) in pairs]
            print(f"[fusion_worker] wrote {len(out)} fused rows @ {datetime.utcnow().isoformat()}")
        except Exception as e:
            print("[fusion_worker] error:", e)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
