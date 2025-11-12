# =====================================================
# 🧠 BuckDuit Final Core (Stage 13.39.5 – Telegram + Insight Polished)
# =====================================================
import os
import asyncio
import threading
import time
from flask import Flask, jsonify
from dotenv import load_dotenv
from supabase import create_client, Client
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from smart_summary import InsightEngine

# =====================================================
# 🧩 Async policy fix for Python 3.12 on Windows
# =====================================================
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# =====================================================
# 🌍 ENVIRONMENT SETUP
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # numeric ID from @userinfobot

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("⚠️ Missing Supabase credentials. Check your .env file.")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("⚠️ Missing Telegram credentials. Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

# =====================================================
# 🧩 SUPABASE CLIENT INIT
# =====================================================
sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
print("✅ Supabase connected.")

# =====================================================
# 🌐 FLASK INIT
# =====================================================
app = Flask(__name__)

@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "BuckDuit Final Core"})

# =====================================================
# ✉️ TELEGRAM SEND WRAPPER
# =====================================================
async def send_telegram_message(message: str):
    """Send message to human user (not another bot)."""
    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.send_message(chat_id=int(CHAT_ID), text=message)
    except Exception as e:
        print(f"⚠️ Telegram send error: {e}")

# =====================================================
# 🔮 AI INSIGHT ENGINE
# =====================================================
engine = InsightEngine(sb, send_telegram_message)

# =====================================================
# 🤖 TELEGRAM BOT COMMANDS
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salam! BuckDuit Final Core is online and ready to monitor insights.")

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace("/feedback", "").strip()
    if not text:
        await update.message.reply_text("Please provide feedback text, e.g. `/feedback Fiverr good`")
        return
    await update.message.reply_text(f"🧾 Feedback received: {text}")
    await engine.process_feedback(text)

# =====================================================
# 🧵 TELEGRAM BOT RUNNER (async-safe)
# =====================================================
def run_bot():
    async def main():
        print("🚀 Starting Telegram bot...")
        bot_app = Application.builder().token(BOT_TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("feedback", feedback))
        print("🤖 Telegram bot connected successfully. Listening now...")
        await bot_app.run_polling(close_loop=False)

    def runner():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(main())
        except Exception as e:
            print(f"⚠️ Telegram thread error: {e}")

    threading.Thread(target=runner, daemon=True).start()

# =====================================================
# 🧠 INSIGHT WORKER LOOP
# =====================================================
def run_insight_worker():
    print("🧠 InsightWorker started (monitoring feedback_events table)...")
    while True:
        try:
            engine.run_once()
        except Exception as e:
            print(f"⚠️ Insight loop error: {e}")
        time.sleep(60)

# =====================================================
# 🚀 MAIN ENTRY POINT
# =====================================================
if __name__ == "__main__":
    print("✅ BuckDuit Final Core initializing...")

    # Start Telegram Bot
    run_bot()

    # Start Insight Worker
    threading.Thread(target=run_insight_worker, daemon=True).start()

    # Start Flask
    print("🧠 Flask backend starting...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
