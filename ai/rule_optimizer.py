# backend/ai/rule_optimizer.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import os
from datetime import datetime, timezone

from utils.supa_client import supabase

MIN_THRESHOLD = 0.50
MAX_THRESHOLD = 0.98
STEP_TIGHTEN  = 0.05   # raise threshold when too chatty / weak confidence
STEP_LOOSEN   = 0.05   # lower threshold when too silent but high confidence
TARGET_MIN_TRIGGERS_24H = 3
TARGET_MAX_TRIGGERS_24H = 50
CONF_MARGIN = 0.10     # "confidence comfortably above threshold" buffer

@dataclass
class RuleStat:
    rule_id: int
    rule_name: str
    current_threshold: float
    triggers: int
    avg_confidence: Optional[float]  # may be None if no triggers

@dataclass
class ProposedChange:
    rule_id: int
    rule_name: str
    old_threshold: float
    new_threshold: float
    reason: str

def _fetch_stats_24h() -> List[RuleStat]:
    resp = supabase.table("v_rule_stats_24h").select("*").execute()
    rows = getattr(resp, "data", []) or []
    stats: List[RuleStat] = []
    for r in rows:
        stats.append(
            RuleStat(
                rule_id=r["rule_id"],
                rule_name=r["rule_name"],
                current_threshold=float(r["current_threshold"]) if r["current_threshold"] is not None else 0.8,
                triggers=int(r["triggers"]) if r["triggers"] is not None else 0,
                avg_confidence=float(r["avg_confidence"]) if r["avg_confidence"] is not None else None,
            )
        )
    return stats

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def compute_proposals() -> List[ProposedChange]:
    proposals: List[ProposedChange] = []
    stats = _fetch_stats_24h()

    for s in stats:
        old = s.current_threshold
        new = old
        reason_chunks = []

        # No triggers → system silent
        if s.triggers == 0:
            # only loosen if we had high avg_confidence historically in 7d window
            # Fallback to slight loosen to probe
            new = _clamp(old - STEP_LOOSEN, MIN_THRESHOLD, MAX_THRESHOLD)
            reason_chunks.append("no_triggers_24h → loosen")

        # Too few triggers but high avg confidence → loosen
        elif s.triggers < TARGET_MIN_TRIGGERS_24H:
            if s.avg_confidence is not None and s.avg_confidence >= (old + CONF_MARGIN):
                new = _clamp(old - STEP_LOOSEN, MIN_THRESHOLD, MAX_THRESHOLD)
                reason_chunks.append("low_volume+high_conf → loosen")

        # Too many triggers and confidence not much above threshold → tighten
        elif s.triggers > TARGET_MAX_TRIGGERS_24H:
            if s.avg_confidence is None or s.avg_confidence < (old + CONF_MARGIN):
                new = _clamp(old + STEP_TIGHTEN, MIN_THRESHOLD, MAX_THRESHOLD)
                reason_chunks.append("high_volume+weak_conf → tighten")

        # If nothing decided, keep
        if new != old:
            proposals.append(
                ProposedChange(
                    rule_id=s.rule_id,
                    rule_name=s.rule_name,
                    old_threshold=old,
                    new_threshold=new,
                    reason="; ".join(reason_chunks) if reason_chunks else "auto-tune"
                )
            )

    return proposals

def apply_proposals(proposals: List[ProposedChange]) -> int:
    count = 0
    for p in proposals:
        if p.new_threshold == p.old_threshold:
            continue
        supabase.table("policy_rules").update(
            {"threshold": p.new_threshold}
        ).eq("id", p.rule_id).execute()
        # system_logs book-keeping (optional but useful)
        _log_system(
            category="optimizer",
            message=f"Threshold updated for rule '{p.rule_name}' {p.old_threshold:.2f} → {p.new_threshold:.2f} ({p.reason})",
            meta={"rule_id": p.rule_id, "old": p.old_threshold, "new": p.new_threshold}
        )
        count += 1
    return count

def _log_system(category: str, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
    supabase.table("system_logs").insert({
        "severity": "info",
        "category": category,
        "message": message,
        "meta": meta or {},
    }).execute()

def run_optimizer(apply: bool = False) -> Dict[str, Any]:
    proposals = compute_proposals()
    result = {
        "time": datetime.now(timezone.utc).isoformat(),
        "proposals": [p.__dict__ for p in proposals],
        "applied": 0,
        "mode": "apply" if apply else "dry-run"
    }
    if apply and proposals:
        result["applied"] = apply_proposals(proposals)
    return result
