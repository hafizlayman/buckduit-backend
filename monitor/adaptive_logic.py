# adaptive_logic.py
from __future__ import annotations
import re, math

# Globals for keyword sets and weights
NEG_WORDS = []
POS_WORDS = []
SCAM_KEYS = []
SRC_WEIGHTS = {}

# -----------------------------
# 🔧 ENV CONFIG LOADER
# -----------------------------
def _parse_csv(s: str) -> list[str]:
    return [x.strip().lower() for x in (s or "").split(",") if x.strip()]

def load_knobs(env):
    """Load environment keyword lists and weights"""
    global NEG_WORDS, POS_WORDS, SCAM_KEYS, SRC_WEIGHTS

    SCAM_KEYS = _parse_csv(env.get("KEYWORDS_SCAM", "scam,fraud,ban,blocked,not paid,no pay,withhold"))
    POS_WORDS = _parse_csv(env.get("KEYWORDS_GOOD", "legit,paid,payout,on time,fast approve"))
    NEG_WORDS = _parse_csv(env.get("KEYWORDS_NEG", "bad,scam,blocked,ban,delay,late,no pay,unpaid"))

    # Parse weights like Fiverr:1.0,Toloka:0.8
    SRC_WEIGHTS = {}
    for item in _parse_csv(env.get("SOURCE_WEIGHTS", "Fiverr:1.0,Toloka:0.9,Remotasks:0.8,Other:0.7")):
        if ":" in item:
            k, v = item.split(":", 1)
            try:
                SRC_WEIGHTS[k.lower()] = float(v)
            except:
                pass

# -----------------------------
# 💬 BASIC SENTIMENT
# -----------------------------
def weight_for_source(source: str) -> float:
    return SRC_WEIGHTS.get((source or "").lower(), 1.0)

def simple_sentiment(text: str) -> float:
    """Cheap sentiment estimator: returns -1.0..+1.0"""
    t = (text or "").lower()
    if not t:
        return 0.0
    score = 0.0
    for w in POS_WORDS:
        if re.search(rf"\b{re.escape(w)}\b", t):
            score += 1.0
    for w in NEG_WORDS:
        if re.search(rf"\b{re.escape(w)}\b", t):
            score -= 1.2
    return max(-1.0, min(1.0, score / 3.0))

# -----------------------------
# ⚠️ SCAM DETECTION
# -----------------------------
def detect_scam_keywords(text: str) -> list[str]:
    t = (text or "").lower()
    hits = [k for k in SCAM_KEYS if k in t]
    return hits

# -----------------------------
# 📊 STATS UTILITIES
# -----------------------------
def rolling_stats(values: list[float]) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    mean = sum(values) / len(values)
    var = sum((x - mean) ** 2 for x in values) / max(1, len(values) - 1)
    std = math.sqrt(var)
    return (mean, std)

def zscore(x: float, mean: float, std: float) -> float:
    if std <= 1e-9:
        return 0.0
    return (x - mean) / std
