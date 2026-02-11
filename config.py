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

# Easily extensible for other roles
ALTERNATE_ROLES = ["Data Scientist", "Business Analyst"]

# ─── Rate Limiting ───────────────────────────────────────────────────
REQUEST_DELAY_MIN = 2  # Minimum seconds between requests
REQUEST_DELAY_MAX = 5  # Maximum seconds between requests
MAX_RETRIES = 3        # Max retries per request
RETRY_DELAY = 5        # Seconds to wait before retrying

# ─── Pagination ──────────────────────────────────────────────────────
MAX_PAGES = 5  # Maximum pages to scrape per platform

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

def get_naukri_url(role, page=1):
    """Generate Naukri.com search URL."""
    role_slug = role.lower().replace(" ", "-")
    exp = SEARCH_EXPERIENCE
    if page == 1:
        return f"https://www.naukri.com/{role_slug}-jobs-in-india?experience={exp}"
    return f"https://www.naukri.com/{role_slug}-jobs-in-india-{page}?experience={exp}"


def get_indeed_url(role, page=0):
    """Generate Indeed India search URL."""
    query = role.replace(" ", "+")
    # sccl=entry_level is the parameter for Indeed India experience level filtering
    return f"https://in.indeed.com/jobs?q={query}&l=India&sccl=entry_level&start={page * 10}"


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
    "Salary Package",
    "Job Link",
]

# ─── Date Category Labels ───────────────────────────────────────────
DATE_CATEGORIES = {
    0: "Posted Today",
    1: "Posted Yesterday",
    2: "Posted 2 Days Ago",
    "3-7": "Posted 3-7 Days Ago",
    "7+": "Posted More Than 1 Week Ago",
}

# ─── Logging ─────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
