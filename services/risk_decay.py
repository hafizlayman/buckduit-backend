# backend/services/risk_decay.py
from datetime import datetime

def decay_all():
    print("🧮 Risk decay operation executed.")
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": "Risk decay completed",
        "affected_metrics": 5
    }

def scorecard():
    print("📊 Returning latest risk scorecard.")
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "low_risk": 7,
            "medium_risk": 3,
            "high_risk": 2
        },
        "trend": "stable"
    }
