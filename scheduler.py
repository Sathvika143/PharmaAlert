"""
Scheduler: Run daily checks for expiry and low-stock medicines.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from notifier import check_and_notify
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use timezone from environment variable or default to Asia/Kolkata (IST)
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "Asia/Kolkata")
scheduler = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE)


def start_scheduler():
    """Start the background scheduler."""
    if not scheduler.running:
        # Run check_and_notify daily at 8:00 AM
        scheduler.add_job(
            check_and_notify,
            CronTrigger(hour=8, minute=0),
            id="daily_medicine_check",
            name="Daily Medicine Expiry & Stock Check",
            replace_existing=True
        )
        scheduler.start()
        logger.info("Scheduler started. Daily check scheduled for 08:00 AM.")


def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped.")
