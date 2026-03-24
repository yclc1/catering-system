"""APScheduler tasks for periodic jobs."""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import async_session
from app.services.reminder_service import check_contract_reminders, check_vehicle_reminders
from app.services.wechat_service import process_notification_queue

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_reminder_checks():
    """Check all reminders and queue notifications."""
    try:
        async with async_session() as session:
            await check_contract_reminders(session)
            await check_vehicle_reminders(session)
            logger.info("Reminder checks completed")
    except Exception as e:
        logger.error(f"Reminder check failed: {e}")


async def run_notification_processing():
    """Process the notification queue."""
    try:
        async with async_session() as session:
            await process_notification_queue(session)
            logger.info("Notification processing completed")
    except Exception as e:
        logger.error(f"Notification processing failed: {e}")


def start_scheduler():
    """Start the scheduler with configured jobs."""
    # Check reminders every hour
    scheduler.add_job(run_reminder_checks, CronTrigger(minute=0), id="reminder_checks", replace_existing=True)

    # Process notification queue every 10 minutes
    scheduler.add_job(run_notification_processing, CronTrigger(minute="*/10"), id="notification_processing", replace_existing=True)

    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
