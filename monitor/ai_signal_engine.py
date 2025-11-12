import os, datetime
from supabase import create_client, Client
from statistics import mean

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# store last few confidence samples in memory
recent_confidences = {}

def analyze_trend(sector: str, confidence: float):
    """Analyze confidence trend and insert AI signal."""
    now = datetime.datetime.utcnow()
    sector_key = sector.lower()

    # update memory
    if sector_key not in recent_confidences:
        recent_confidences[sector_key] = []
    recent_confidences[sector_key].append(confidence)
    if len(recent_confidences[sector_key]) > 5:
        recent_confidences[sector_key].pop(0)

    trend, risk, note = compute_signal(recent_confidences[sector_key])

    data = {
        "timestamp": now.isoformat(),
        "sector": sector,
        "confidence": confidence,
        "trend": trend,
        "signal": f"{trend.upper()}_{risk.upper()}",
        "risk_level": risk,
        "note": note,
    }
    try:
        supabase.table("ai_signals").insert(data).execute()
        print(f"🧩 AI Signal Recorded: {sector} → {trend}/{risk}")
    except Exception as e:
        print(f"⚠️ AI signal log failed: {e}")

def compute_signal(history):
    """Return trend, risk, note based on confidence history."""
    if len(history) < 3:
        return "insufficient", "unknown", "Need more data"

    delta = history[-1] - history[-2]
    avg = mean(history)

    # determine trend
    if delta > 0.05:
        trend = "rising"
    elif delta < -0.05:
        trend = "falling"
    else:
        trend = "stable"

    # risk classification
    if avg >= 0.8:
        risk = "low"
    elif avg >= 0.6:
        risk = "medium"
    elif avg >= 0.4:
        risk = "high"
    else:
        risk = "critical"

    note = f"Δ {delta:+.2f} / avg {avg:.2f}"
    return trend, risk, note
