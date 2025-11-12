import time, json
from utils.supa_client import supabase

def sync_rules(interval=300):
    print("🔄 Policy Rule Sync Worker started...")
    while True:
        try:
            res = supabase.table("policy_rules").select("*").execute()
            if res.data:
                with open("data/rules.json", "w") as f:
                    json.dump(res.data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Rule sync failed: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    sync_rules()
