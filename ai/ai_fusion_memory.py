import json, os
from datetime import datetime
from collections import deque

MEMORY_FILE = "fusion_memory.json"
MAX_MEMORY = 10

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return deque(maxlen=MAX_MEMORY)
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            return deque(data, maxlen=MAX_MEMORY)
    except json.JSONDecodeError:
        return deque(maxlen=MAX_MEMORY)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(list(memory), f, indent=2)

def get_fusion_memory():
    return list(load_memory())

def update_fusion_memory(current_fusion, confidence, risk_delta):
    memory = load_memory()
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "fusion": round(current_fusion, 2),
        "confidence": round(confidence, 2),
        "risk_delta": round(risk_delta, 2)
    }
    memory.append(entry)
    save_memory(memory)
    return list(memory)
