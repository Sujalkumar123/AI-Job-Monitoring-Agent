"""
Main orchestrator for the Job Monitoring Agent.
Runs all scrapers across ALL analyst roles, processes results, and exports to Excel/CSV.
"""

import os
import sys
import logging
from datetime import datetime

import config
from scrapers import NaukriScraper, IndeedScraper, LinkedInScraper, WellfoundScraper
from processor import process_jobs, merge_with_existing
from exporter import export_to_excel, export_to_csv
import lead_finder

# ─── Logging Setup ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(config.BASE_DIR, "agent.log"),
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("JobAgent")


def run_agent(role: str = None, location: str = None, days_ago: int = 7):
    """
    Main agent execution:
    1. Scrape all platforms (each scraper handles ALL roles internally)
    2. Process and deduplicate
    3. Merge with existing data
    4. Export to Excel + CSV
    
    Args:
        role: Not used anymore (each scraper iterates all roles from config)
        location: Location filter (default from config)
        days_ago: How many days back to search (default 7)
    """
    location = location or config.SEARCH_LOCATION

    logger.info("=" * 70)
    logger.info(f"🚀 Job Monitoring Agent Started")
    logger.info(f"   Roles: {len(config.ALL_SEARCH_ROLES)} analyst roles")
    logger.info(f"   Location: {location}")
    logger.info(f"   Time Filter: Last {days_ago} days")
    logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    # ── 1. Scrape all platforms (each handles multi-role internally) ──
    all_jobs = []
    scrapers = [
        ("Naukri", NaukriScraper()),
        ("Indeed", IndeedScraper()),
        ("LinkedIn", LinkedInScraper()),
        ("Wellfound", WellfoundScraper()),
    ]

    platform_stats = {}

    for name, scraper in scrapers:
        try:
            logger.info(f"\n{'─' * 50}")
            logger.info(f"📋 Scraping: {name} (all analyst roles)")
            logger.info(f"{'─' * 50}")

            jobs = scraper.scrape(location=location, days_ago=days_ago)
            platform_stats[name] = len(jobs)
            all_jobs.extend(jobs)

            logger.info(f"✅ {name}: {len(jobs)} jobs found across all roles")

        except Exception as e:
            logger.error(f"❌ {name} scraper failed: {e}")
            platform_stats[name] = 0

    logger.info(f"\n📊 Raw totals: {len(all_jobs)} jobs from {len(scrapers)} platforms")

    # ── 2. Process (normalize, categorize, deduplicate) ──
    processed_jobs = process_jobs(all_jobs)

    # ── 3. Merge with existing data ──
    if os.path.exists(config.OUTPUT_FILE):
        final_jobs = merge_with_existing(processed_jobs, config.OUTPUT_FILE)
    else:
        final_jobs = processed_jobs

    # ── 3. Find HR Leads (Cold Mailing) ──
    logger.info("🔍 Finding HR Contact Emails for new jobs...")
    try:
        lead_finder.update_leads_file()
    except Exception as e:
        logger.error(f"Error finding HR leads: {e}")
        
    # ── 4. Export ──
    excel_path = "N/A"
    csv_path = "N/A"
    
    try:
        excel_path = export_to_excel(final_jobs)
    except Exception as e:
        logger.error(f"⚠️ Could not update Excel file (maybe it is open?): {e}")
        
    try:
        csv_path = export_to_csv(final_jobs)
    except Exception as e:
        logger.error(f"⚠️ Could not update CSV file: {e}")

    # ── 5. Summary ──
    logger.info("\n" + "=" * 70)
    logger.info("📈 AGENT SUMMARY")
    logger.info("=" * 70)
    for platform, count in platform_stats.items():
        logger.info(f"   {platform:15s}: {count:4d} jobs scraped")
    logger.info(f"   {'─' * 30}")
    logger.info(f"   {'Raw Total':15s}: {len(all_jobs):4d} jobs")
    logger.info(f"   {'After Processing':15s}: {len(processed_jobs):4d} jobs")
    logger.info(f"   {'Final (merged)':15s}: {len(final_jobs):4d} jobs")
    logger.info(f"\n   📁 Excel: {excel_path}")
    logger.info(f"   📁 CSV:   {csv_path}")
    logger.info("=" * 70)

    return final_jobs


if __name__ == "__main__":
    # Allow custom days_ago from command line
    # Usage: python main.py 7  (for last 7 days)
    custom_days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    run_agent(days_ago=custom_days)
