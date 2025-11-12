# backend/workers/rule_optimizer_worker.py
import os, time, traceback
from ai.rule_optimizer import run_optimizer

INTERVAL_SECONDS = int(os.getenv("RULE_OPTIMIZER_INTERVAL_SEC", "900"))  # 15 min default

def main():
    print(f"🔧 Rule Optimizer worker starting… interval={INTERVAL_SECONDS}s")
    while True:
        try:
            result = run_optimizer(apply=True)
            print("✅ optimizer_result:", result)
        except Exception as e:
            print("❌ optimizer_error:", e)
            traceback.print_exc()
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
