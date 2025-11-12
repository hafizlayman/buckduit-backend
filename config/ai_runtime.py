    # backend/config/ai_runtime.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from threading import RLock
from typing import Dict, Any

@dataclass
class RuntimeParams:
    target_accuracy: float = 0.92
    max_bias: float = 0.15
    learning_rate: float = 0.05
    correction_weight: float = 0.50

class _Registry:
    def __init__(self):
        self._lock = RLock()
        self._params = RuntimeParams()

    def get(self) -> Dict[str, Any]:
        with self._lock:
            return asdict(self._params)

    def update(self, **kwargs) -> Dict[str, Any]:
        with self._lock:
            for k, v in kwargs.items():
                if hasattr(self._params, k) and v is not None:
                    setattr(self._params, k, float(v))
            return asdict(self._params)

REGISTRY = _Registry()

def get_params() -> Dict[str, Any]:
    return REGISTRY.get()

def update_params_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    if not row:
        return get_params()
    return REGISTRY.update(
        target_accuracy=row.get("target_accuracy"),
        max_bias=row.get("max_bias"),
        learning_rate=row.get("learning_rate"),
        correction_weight=row.get("correction_weight"),
    )
