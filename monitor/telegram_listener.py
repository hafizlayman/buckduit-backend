# ============================================
# 🧠 BuckDuit Telegram Feedback Listener (Stable for Windows + Flask)
# ============================================
async def start(update, context):
    await update.message.reply_text(
        "🤖 BuckDuit AI is online.\nUse /feedback [app] [good/bad]"
    )

async def feedback(update, context):
    try:
        if len(context.args) != 2:
            await update.message.reply_text("❌ Usage: /feedback [app] [good/bad]")
            return

        app_name = context.args[0].capitalize()
        sentiment = context.args[1].lower()

        if sentiment not in ["good", "bad"]:
            await update.message.reply_text("⚠️ Sentiment must be 'good' or 'bad'")
            return

        change = 0.05 if sentiment == "good" else -0.05

        result = supabase.table("offers").update({
            "weighted_confidence": supabase.func.coalesce("weighted_confidence", 0) + change
        }).eq("app_name", app_name).execute()

        await update.message.reply_text(f"✅ {app_name} updated: {change:.2f} ({sentiment})")
        print(f"✅ Telegram feedback processed for {app_name} ({sentiment})")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        print(f"[Feedback Error] {e}")

def run_telegram_bot():
    """Runs the Telegram bot in an async event loop (safe for Windows)."""
    async def main():
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("feedback", feedback))

        print("🤖 Telegram bot started. Listening for commands...")
        await application.run_polling(stop_signals=None)  # prevents signal/thread issues

    asyncio.run(main())

def start_telegram_in_thread():
    thread = threading.Thread(target=run_telegram_bot, daemon=True)
    thread.start()
    print("🚀 Telegram listener thread launched successfully.")
