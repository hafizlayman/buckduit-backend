import os, time, requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("⚠️ Set TELEGRAM_BOT_TOKEN in .env first")
    exit()

print("Polling Telegram... send any message to your bot now.")
offset = None
while True:
    try:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset": offset or ""}).json()
        for u in r.get("result", []):
            offset = u["update_id"] + 1
            msg = u.get("message")
            if msg:
                print("💬 chat_id:", msg["chat"]["id"], "| text:", msg.get("text"))
    except Exception as e:
        print("Error:", e)
    time.sleep(2)
