# ai/predictive_failure_ai.py
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Features:
render_uptime_5m: float # 0..1
backend_http_ok_rate: float # 0..1
supabase_write_p50_ms: float # milliseconds
supabase_write_p95_ms: float # milliseconds
tele_success_rate: float # 0..1
err_rate_last10m: float # 0..1
retries_last10m: int
cpu_pct: float # 0..100
mem_pct: float # 0..100


class PredictiveFailureModel:
"""Lightweight scorer producing risk in [0,1].
Uses normalized features + calibrated logistic mapping.
"""
def __init__(self) -> None:
# Baseline weights (hand‑tuned, can be learned offline)
self.w = {
"render_uptime_5m": -2.4,
"backend_http_ok_rate": -2.0,
"supabase_write_p50_ms": +0.0012,
"supabase_write_p95_ms": +0.0020,
"tele_success_rate": -1.6,
"err_rate_last10m": +2.6,
"retries_last10m": +0.08,
"cpu_pct": +0.02,
"mem_pct": +0.015,
}
self.bias = -0.8


def _logit(self, f: Dict[str, float]) -> float:
z = self.bias
for k, v in self.w.items():
z += v * f.get(k, 0.0)
return z


@staticmethod
def _sigmoid(z: float) -> float:
return 1.0 / (1.0 + np.exp(-z))


def score(self, feats: Features) -> dict:
f = {
"render_uptime_5m": float(feats.render_uptime_5m),
"backend_http_ok_rate": float(feats.backend_http_ok_rate),
"supabase_write_p50_ms": float(feats.supabase_write_p50_ms),
"supabase_write_p95_ms": float(feats.supabase_write_p95_ms),
"tele_success_rate": float(feats.tele_success_rate),
"err_rate_last10m": float(feats.err_rate_last10m),
"retries_last10m": float(feats.retries_last10m),
"cpu_pct": float(feats.cpu_pct),
"mem_pct": float(feats.mem_pct),
}
z = self._logit(f)
risk = float(self._sigmoid(z))
if risk < 0.33:
verdict = "ok"
elif risk < 0.66:
return {"risk": risk, "verdict": verdict, "features": f, "z": z}