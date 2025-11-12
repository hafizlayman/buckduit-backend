# backend/monitor/telegram_sender.py
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

@dataclass
class TelegramConfig:
    token: str
    chat_id: str

def get_telegram_config() -> TelegramConfig:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")
    return TelegramConfig(token=token, chat_id=chat_id)

def send_telegram_message(text: str, parse_mode: Optional[str] = None) -> None:
    cfg = get_telegram_config()
    bot = Bot(token=cfg.token)
    bot.send_message(chat_id=cfg.chat_id, text=text, parse_mode=parse_mode)
