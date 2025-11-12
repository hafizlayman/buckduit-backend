# backend/monitor/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
from services.auto_thresholds import run_auto_tune
from services.risk_decay import decay_all

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.UTC)
    
    # Run decay every 15 minutes
    scheduler.add_job(lambda: decay_all(), CronTrigger(minute="*/15"))
    
    # Run auto-tune every 2 hours
    scheduler.add_job(lambda: run_auto_tune(), CronTrigger(hour="*/2", minute=5))
    
    scheduler.start()
    print(f"🕒 Scheduler started at {datetime.utcnow().isoformat()} UTC")
    return scheduler
