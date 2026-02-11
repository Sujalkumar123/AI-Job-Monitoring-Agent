"""
Scheduler module for running the Job Monitoring Agent daily.
Uses the `schedule` library for simple, reliable scheduling.

Usage:
    python scheduler.py           # Start the scheduler (runs daily at configured time)
    python main.py                # Run once immediately
"""

import time
import logging
import schedule

import config
from main import run_agent

logger = logging.getLogger("Scheduler")


def scheduled_job():
    """Wrapper for the scheduled agent run."""
    logger.info("⏰ Scheduled run triggered!")
    try:
        run_agent()
        logger.info("✅ Scheduled run completed successfully")
    except Exception as e:
        logger.error(f"❌ Scheduled run failed: {e}")


def start_scheduler():
    """Start the daily scheduler."""
    run_time = config.SCHEDULE_TIME

    logger.info(f"🗓️  Scheduler started — will run daily at {run_time}")
    logger.info(f"   Role: {config.SEARCH_ROLE}")
    logger.info(f"   Location: {config.SEARCH_LOCATION}")
    logger.info(f"   Press Ctrl+C to stop")

    schedule.every().day.at(run_time).do(scheduled_job)

    # Also run immediately on first start
    logger.info("▶️  Running initial scrape now...")
    scheduled_job()

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    start_scheduler()
