from datetime import datetime

def apply_feedback_learning(supabase, app_name, sentiment):
    """
    Adjusts confidence levels in the offers table based on feedback.
    Handles missing (None) ai_confidence safely.
    """
    try:
        delta = 0.05 if sentiment.lower() == "good" else -0.05

        data = supabase.table("offers").select("*").eq("name", app_name).execute()
        if not data.data:
            return f"⚠️ No record found for '{app_name}'."

        record = data.data[0]

        # --- Fix: handle None gracefully ---
        current_conf = record.get("ai_confidence")
        if current_conf is None:
            current_conf = 0.0
        else:
            current_conf = float(current_conf)

        # Clamp to [0,1] range
        new_conf = max(0.0, min(1.0, current_conf + delta))

        # Update offers table
        supabase.table("offers").update({"ai_confidence": new_conf}).eq("name", app_name).execute()

        # Log feedback
        supabase.table("feedback_logs").insert({
            "app_name": app_name,
            "sentiment": sentiment,
            "confidence_delta": delta,
            "created_at": datetime.now().isoformat()
        }).execute()

        trend_emoji = "📈" if delta > 0 else "📉"
        return f"{trend_emoji} {app_name} updated: {current_conf:.2f} → {new_conf:.2f} ({sentiment})"

    except Exception as e:
        return f"❌ Feedback error: {str(e)}"
