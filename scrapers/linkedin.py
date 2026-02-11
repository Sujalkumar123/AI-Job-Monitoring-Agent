"""
LinkedIn scraper using the python-jobspy library.
python-jobspy handles LinkedIn's anti-scraping measures internally.
"""

import logging

import config
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn jobs using python-jobspy."""

    PLATFORM_NAME = "LinkedIn"

    def scrape(self, role: str = None, location: str = None) -> list[dict]:
        """Scrape Data Analyst jobs from LinkedIn via python-jobspy."""
        role = role or config.SEARCH_ROLE
        location = location or config.SEARCH_LOCATION
        all_jobs = []

        try:
            from jobspy import scrape_jobs

            logger.info(f"[LinkedIn] Scraping via python-jobspy: '{role}' in '{location}'")

            results = scrape_jobs(
                site_name=["linkedin"],
                search_term=role,
                location=location,
                results_wanted=50,
                country_indeed="India",
                hours_old=168,  # Last 7 days
                experience_levels=["entry_level"],
            )

            if results is not None and not results.empty:
                for _, row in results.iterrows():
                    try:
                        job = self._convert_row(row)
                        if job and job.get("Company Name"):
                            all_jobs.append(job)
                    except Exception as e:
                        logger.debug(f"[LinkedIn] Error converting row: {e}")
                        continue

            logger.info(f"[LinkedIn] Total jobs scraped: {len(all_jobs)}")

        except ImportError:
            logger.error("[LinkedIn] python-jobspy not installed. Run: pip install python-jobspy")
        except Exception as e:
            logger.error(f"[LinkedIn] Scraping failed: {e}")

        return all_jobs

    def _convert_row(self, row) -> dict | None:
        """Convert a python-jobspy DataFrame row to our standard format."""
        company = str(row.get("company", "")).strip() if row.get("company") else None
        title = str(row.get("title", "")).strip() if row.get("title") else None
        location_val = str(row.get("location", "")).strip() if row.get("location") else ""

        # Salary
        salary = None
        min_sal = row.get("min_amount")
        max_sal = row.get("max_amount")
        currency = row.get("currency", "")
        interval = row.get("interval", "")

        if min_sal and max_sal:
            salary = f"{currency}{min_sal:,.0f} - {currency}{max_sal:,.0f}"
            if interval:
                salary += f" ({interval})"
        elif min_sal:
            salary = f"{currency}{min_sal:,.0f}"
            if interval:
                salary += f" ({interval})"

        # Date
        date_posted = ""
        if row.get("date_posted"):
            try:
                date_posted = str(row["date_posted"])
            except Exception:
                pass

        # Link
        link = str(row.get("job_url", "")).strip() if row.get("job_url") else ""

        if not company and not title:
            return None

        return self.make_job_record(
            company=company or "Unknown",
            title=title or "Data Analyst",
            location=location_val,
            platform=self.PLATFORM_NAME,
            date_posted=date_posted,
            salary=salary,
            link=link,
        )
