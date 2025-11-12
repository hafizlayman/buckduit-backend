from utils.supa_client import supabase  # ✅ Corrected path
from services.notifier import send_telegram_message
import time
from datetime import datetime

def process_event(event_type, payload):
    try:
        timestamp = datetime.utcnow().isoformat()
        print(f"[Policy Engine] Event: {event_type} at {timestamp}")

        if event_type == "policy_violation":
            handle_policy_violation(payload)
        elif event_type == "drift_detected":
            handle_drift_alert(payload)
        elif event_type == "system_failure":
            handle_system_failure(payload)
        else:
            print(f"[Policy Engine] Unknown event type: {event_type}")

        supabase.table("system_logs").insert({
            "event_type": event_type,
            "payload": payload,
            "created_at": timestamp
        }).execute()

    except Exception as e:
        print(f"[Policy Engine] Error: {e}")
        send_telegram_message(f"⚠️ Policy Engine Error: {e}")


def handle_policy_violation(payload):
    send_telegram_message(f"🚨 Policy Violation: {payload}")
    time.sleep(0.5)

def handle_drift_alert(payload):
    send_telegram_message(f"📉 Drift Alert: {payload}")
    time.sleep(0.5)

def handle_system_failure(payload):
    send_telegram_message(f"💥 System Failure: {payload}")
    time.sleep(0.5)
