"""
Base scraper class with common functionality:
- Session management with User-Agent rotation
- Rate limiting between requests
- Retry logic with exponential backoff
- Standardized job record format
"""

import time
import random
import logging
import requests
from abc import ABC, abstractmethod

import config

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""

    PLATFORM_NAME = "Unknown"

    def __init__(self):
        self.session = requests.Session()
        self._rotate_user_agent()

    def _rotate_user_agent(self):
        """Set a random User-Agent header."""
        ua = random.choice(config.USER_AGENTS)
        self.session.headers.update({
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
        })

    def _rate_limit(self):
        """Sleep for a random duration between requests."""
        delay = random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX)
        logger.debug(f"Rate limiting: sleeping {delay:.1f}s")
        time.sleep(delay)

    def _fetch(self, url: str, **kwargs) -> requests.Response | None:
        """
        Fetch a URL with retries and rate limiting.
        Returns Response on success, None on failure.
        """
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                self._rotate_user_agent()
                logger.info(f"[{self.PLATFORM_NAME}] Fetching: {url} (attempt {attempt})")
                resp = self.session.get(url, timeout=30, **kwargs)

                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 403:
                    logger.warning(f"[{self.PLATFORM_NAME}] 403 Forbidden — may be blocked")
                    time.sleep(config.RETRY_DELAY * attempt)
                elif resp.status_code == 429:
                    logger.warning(f"[{self.PLATFORM_NAME}] 429 Too Many Requests — backing off")
                    time.sleep(config.RETRY_DELAY * attempt * 2)
                else:
                    logger.warning(f"[{self.PLATFORM_NAME}] HTTP {resp.status_code}")
                    time.sleep(config.RETRY_DELAY)

            except requests.RequestException as e:
                logger.error(f"[{self.PLATFORM_NAME}] Request error: {e}")
                time.sleep(config.RETRY_DELAY * attempt)

        logger.error(f"[{self.PLATFORM_NAME}] Failed after {config.MAX_RETRIES} attempts: {url}")
        return None

    @staticmethod
    def make_job_record(
        company: str,
        title: str,
        location: str,
        platform: str,
        date_posted: str,
        salary: str,
        link: str,
    ) -> dict:
        """Create a standardized job record dictionary."""
        return {
            "Company Name": (company or "").strip(),
            "Job Title": (title or "").strip(),
            "Location": (location or "").strip(),
            "Platform Source": platform,
            "Date Posted": (date_posted or "").strip(),
            "Posting Category": "",  # Filled later by processor
            "Salary Package": (salary or "NULL").strip() if salary else "NULL",
            "Job Link": (link or "").strip(),
        }

    @abstractmethod
    def scrape(self, role: str = None, location: str = None) -> list[dict]:
        """
        Scrape job listings from this platform.

        Args:
            role: Job role to search (default from config)
            location: Location filter (default from config)

        Returns:
            List of job record dicts with standardized keys.
        """
        pass
