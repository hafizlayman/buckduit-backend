# =====================================================
# 🧠 Smart Summary Engine — AI Insight Layer (Final)
# =====================================================
import asyncio

class InsightEngine:
    def __init__(self, supabase_client, telegram_send_fn):
        self.sb = supabase_client
        self.send_message = telegram_send_fn

    # =================================================
    # 🔁 MAIN LOOP
    # =================================================
    def run_once(self):
        print("🔍 Checking new feedback data...")
        try:
            response = self.sb.table("feedback_events").select("*").order("created_at", desc=True).limit(10).execute()

            if response is None or not hasattr(response, "data"):
                print("⚠️ Supabase returned None or invalid response object.")
                return

            rows = response.data
            if not rows:
                print("⚠️ No feedback entries found.")
                return
        except Exception as e:
            print(f"⚠️ Supabase fetch error: {e}")
            return

        alerts = self.analyze_feedback(rows)
        for alert in alerts:
            try:
                asyncio.run(self.send_message(alert))
            except Exception as e:
                print(f"⚠️ Telegram send error: {e}")

    # =================================================
    # 🧩 ANALYSIS LOGIC
    # =================================================
    def analyze_feedback(self, rows):
        alerts = []
        scam_keywords = ["scam", "blocked", "fraud", "suspend", "ban"]
        flagged = []

        for r in rows:
            text = (r.get("text") or "").lower()
            src = r.get("source", "unknown")
            for kw in scam_keywords:
                if kw in text:
                    alerts.append(f"⚠️ Scam-related keyword detected: '{kw}' in '{src}'")
                    flagged.append(text)

        if flagged:
            alerts.append(f"🔻 Total suspicious feedback entries: {len(flagged)}")

        return alerts
