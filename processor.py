"""
Data processor module:
- Converts relative dates to absolute dates
- Categorizes postings by recency
- Deduplicates across platforms using fuzzy matching
- Normalizes salary and validates records
"""

import re
import logging
from datetime import datetime, timedelta, date as DateType
from typing import Optional

import pandas as pd
from fuzzywuzzy import fuzz

import config

logger = logging.getLogger(__name__)

TODAY = datetime.now().date()


def process_jobs(jobs: list[dict]) -> list[dict]:
    """
    Full processing pipeline:
    1. Normalize dates → assign posting category
    2. Normalize salary
    3. Validate records
    4. Deduplicate
    """
    logger.info(f"Processing {len(jobs)} raw jobs...")

    processed = []
    for job in jobs:
        job = _normalize_date(job)
        job = _normalize_salary(job)
        if _is_valid(job):
            processed.append(job)

    logger.info(f"Valid jobs after normalization: {len(processed)}")

    deduped = _deduplicate(processed)
    logger.info(f"Jobs after deduplication: {len(deduped)}")

    return deduped


def _normalize_date(job: dict) -> dict:
    """Convert various date formats to a standard date and assign posting category."""
    raw_date = job.get("Date Posted", "").strip().lower()

    days_ago = None

    if not raw_date:
        job["Date Posted"] = ""
        job["Posting Category"] = "Unknown"
        return job

    # ── Pattern: "X days ago", "X day ago", "Xd ago" ──
    match = re.search(r"(\d+)\s*(?:day|d)s?\s*ago", raw_date)
    if match:
        days_ago = int(match.group(1))

    # ── Pattern: "today", "just now", "just posted" ──
    elif any(kw in raw_date for kw in ["today", "just now", "just posted", "few hours", "hour ago", "hours ago", "0 day"]):
        days_ago = 0

    # ── Pattern: "yesterday" ──
    elif "yesterday" in raw_date:
        days_ago = 1

    # ── Pattern: "X weeks ago" ──
    elif re.search(r"(\d+)\s*week", raw_date):
        weeks = int(re.search(r"(\d+)\s*week", raw_date).group(1))
        days_ago = weeks * 7

    # ── Pattern: "X months ago" ──
    elif re.search(r"(\d+)\s*month", raw_date):
        months = int(re.search(r"(\d+)\s*month", raw_date).group(1))
        days_ago = months * 30

    # ── Pattern: absolute dates "dd mmm yyyy", "yyyy-mm-dd", etc. ──
    else:
        parsed_date = _try_parse_date(raw_date)
        if parsed_date:
            days_ago = (TODAY - parsed_date).days

    # Assign date and category
    if days_ago is not None:
        actual_date = TODAY - timedelta(days=days_ago)
        job["Date Posted"] = actual_date.strftime("%d %b %Y")
        job["Posting Category"] = _categorize_days(days_ago)
    else:
        # Keep original text if we can't parse
        job["Posting Category"] = "Unknown"

    return job


def _try_parse_date(text: str) -> Optional[DateType]:
    """Try parsing a date string with various formats."""
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ]
    # Clean common prefixes
    text = re.sub(r"^(posted\s*on\s*|posted\s*)", "", text.strip())

    for fmt in formats:
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _categorize_days(days_ago: int) -> str:
    """Categorize based on how many days ago the job was posted."""
    if days_ago == 0:
        return "Posted Today"
    elif days_ago == 1:
        return "Posted Yesterday"
    elif days_ago == 2:
        return "Posted 2 Days Ago"
    elif 3 <= days_ago <= 7:
        return "Posted 3-7 Days Ago"
    else:
        return "Posted More Than 1 Week Ago"


def _normalize_salary(job: dict) -> dict:
    """Normalize salary field — mark missing as NULL."""
    salary = job.get("Salary Package", "").strip()
    if not salary or salary.lower() in ["null", "none", "n/a", "not disclosed", "not mentioned", ""]:
        job["Salary Package"] = "NULL"
    return job


def _is_valid(job: dict) -> bool:
    """Validate that the job record has minimum required fields."""
    company = job.get("Company Name", "").strip()
    if not company or company.lower() in ["unknown", ""]:
        return False

    title = job.get("Job Title", "").strip()
    if not title:
        return False

    return True


def _deduplicate(jobs: list[dict]) -> list[dict]:
    """
    Remove duplicate jobs using fuzzy matching on company + title + location.
    When duplicates across platforms are found, keep the one with:
    - More info (salary, date)
    - From the preferred platform priority: Naukri > LinkedIn > Indeed > Wellfound
    """
    if not jobs:
        return jobs

    platform_priority = {"Naukri": 0, "LinkedIn": 1, "Indeed": 2, "Wellfound": 3}
    unique_jobs = []
    seen = []  # List of (company, title, location) tuples of accepted jobs

    # Sort by platform priority first (preferred sources first)
    jobs_sorted = sorted(jobs, key=lambda x: platform_priority.get(x.get("Platform Source", ""), 99))

    for job in jobs_sorted:
        comp = str(job.get("Company Name", "")).lower().strip()
        title = str(job.get("Job Title", "")).lower().strip()
        loc = str(job.get("Location", "")).lower().strip()

        is_dup = False
        for s_comp, s_title, s_loc in seen:
            # Fuzzy match: company (threshold 80), title (threshold 85)
            comp_score = fuzz.ratio(comp, s_comp)
            title_score = fuzz.ratio(title, s_title)

            if comp_score >= 80 and title_score >= 85:
                # Also check location similarity if both have locations
                if loc and s_loc:
                    loc_score = fuzz.ratio(loc, s_loc)
                    if loc_score >= 60:
                        is_dup = True
                        break
                else:
                    is_dup = True
                    break

        if not is_dup:
            unique_jobs.append(job)
            seen.append((comp, title, loc))

    removed = len(jobs) - len(unique_jobs)
    if removed > 0:
        logger.info(f"Removed {removed} duplicate job(s)")

    return unique_jobs


def merge_with_existing(new_jobs: list[dict], existing_file: str) -> list[dict]:
    """
    Merge new jobs with existing data from file.
    Returns only the new jobs that don't already exist.
    """
    try:
        existing_df = pd.read_excel(existing_file)
        existing_records = existing_df.to_dict("records")
        logger.info(f"Loaded {len(existing_records)} existing jobs from file")
    except FileNotFoundError:
        logger.info("No existing file found — all jobs are new")
        return new_jobs
    except Exception as e:
        logger.warning(f"Error reading existing file: {e}")
        return new_jobs

    # Combine existing + new and deduplicate
    all_jobs = existing_records + new_jobs
    deduped = _deduplicate(all_jobs)

    # Return only truly new entries
    new_count = len(deduped) - len(existing_records)
    logger.info(f"Found {max(0, new_count)} new job(s) to append")

    return deduped
