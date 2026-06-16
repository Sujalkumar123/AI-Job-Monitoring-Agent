"""
Configuration module for the Job Monitoring Agent.
Centralizes all search parameters, headers, and settings.
"""

import os
from datetime import datetime

# ─── Search Parameters ───────────────────────────────────────────────
SEARCH_ROLE = "Data Analyst"
SEARCH_LOCATION = "India"
SEARCH_EXPERIENCE = 0  # 0 for Entry Level / Freshers

# ─── All Analyst Roles (SQL / Power BI / Python focused) ────────────
ALL_SEARCH_ROLES = [
    "Data Analyst",
    "Business Analyst",
    "SQL Analyst",
    "BI Analyst",
    "Power BI Developer",
    "Power BI Analyst",
    "MIS Analyst",
    "MIS Executive",
    "Data Scientist",
    "Business Intelligence Analyst",
    "Reporting Analyst",
    "Analytics Analyst",
    "Python Developer",
    "Data Engineer",
    "ETL Developer",
    "Database Analyst",
    "Insights Analyst",
    "Research Analyst",
]

# Skills to look for in job descriptions
SEARCH_SKILLS = ["SQL", "Power BI", "Python"]

# ─── Time Filter Options (for Dashboard) ────────────────────────────
TIME_FILTER_OPTIONS = {
    "Last 1 Day": 1,
    "Last 7 Days": 7,
    "Last 15 Days": 15,
    "Last 1 Month": 30,
    "All Time": 9999,
}

DEFAULT_TIME_FILTER = "Last 7 Days"

# ─── Rate Limiting ───────────────────────────────────────────────────
REQUEST_DELAY_MIN = 1  # Minimum seconds between requests
REQUEST_DELAY_MAX = 2  # Maximum seconds between requests
MAX_RETRIES = 1        # Max retries per request (keep fast)
RETRY_DELAY = 2        # Seconds to wait before retrying

# ─── Pagination ──────────────────────────────────────────────────────
MAX_PAGES = 1  # Maximum pages to scrape per platform per role (1 page = fast)

# ─── Output ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "jobs_data.xlsx")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "jobs_data.csv")

# ─── Scheduler ───────────────────────────────────────────────────────
SCHEDULE_TIME = "09:00"  # Daily run time (24-hour format)

# ─── User-Agent Rotation Pool ────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# ─── Platform-Specific URLs ─────────────────────────────────────────

def get_naukri_url(role, page=1, days_ago=7):
    """Generate Naukri.com search URL with freshness filter."""
    role_slug = role.lower().replace(" ", "-")
    exp = SEARCH_EXPERIENCE
    # Naukri freshness filter
    if days_ago <= 1:
        freshness = 1
    elif days_ago <= 7:
        freshness = 7
    elif days_ago <= 15:
        freshness = 15
    else:
        freshness = 30

    if page == 1:
        return f"https://www.naukri.com/{role_slug}-jobs-in-india?experience={exp}&jobAge={freshness}"
    return f"https://www.naukri.com/{role_slug}-jobs-in-india-{page}?experience={exp}&jobAge={freshness}"


def get_indeed_url(role, page=0, days_ago=7):
    """Generate Indeed India search URL with time filter."""
    query = role.replace(" ", "+")
    # Indeed fromage parameter: number of days
    if days_ago <= 1:
        fromage = 1
    elif days_ago <= 7:
        fromage = 7
    elif days_ago <= 15:
        fromage = 14
    else:
        fromage = 30

    return f"https://in.indeed.com/jobs?q={query}&l=India&sccl=entry_level&fromage={fromage}&start={page * 10}"


def get_wellfound_url(role):
    """Generate Wellfound search URL."""
    role_slug = role.lower().replace(" ", "-")
    return f"https://wellfound.com/role/l/{role_slug}/india"


# ─── Column Names (standardized output) ─────────────────────────────
COLUMNS = [
    "Company Name",
    "Job Title",
    "Location",
    "Platform Source",
    "Date Posted",
    "Posting Category",
    "Days Ago",
    "Salary Package",
    "Job Link",
]

# ─── Date Category Labels ───────────────────────────────────────────
DATE_CATEGORIES = {
    0: "Posted Today",
    1: "Posted Yesterday",
    "2-7": "Posted 2-7 Days Ago",
    "8-15": "Posted 8-15 Days Ago",
    "16-30": "Posted 16-30 Days Ago",
    "30+": "Posted More Than 1 Month Ago",
}

# ─── Logging ─────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
