"""
Naukri.com scraper for job listings.
Uses requests + BeautifulSoup to parse Naukri's search results.
"""

import re
import logging
from bs4 import BeautifulSoup

import config
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class NaukriScraper(BaseScraper):
    """Scraper for Naukri.com job listings."""

    PLATFORM_NAME = "Naukri"

    def scrape(self, role: str = None, location: str = None) -> list[dict]:
        """Scrape Data Analyst jobs from Naukri.com."""
        role = role or config.SEARCH_ROLE
        location = location or config.SEARCH_LOCATION
        all_jobs = []

        for page in range(1, config.MAX_PAGES + 1):
            url = config.get_naukri_url(role, page)
            resp = self._fetch(url)

            if not resp:
                logger.warning(f"[Naukri] Failed to fetch page {page}")
                break

            jobs = self._parse_page(resp.text)
            if not jobs:
                logger.info(f"[Naukri] No jobs found on page {page}, stopping pagination")
                break

            all_jobs.extend(jobs)
            logger.info(f"[Naukri] Page {page}: found {len(jobs)} jobs")
            self._rate_limit()

        logger.info(f"[Naukri] Total jobs scraped: {len(all_jobs)}")
        return all_jobs

    def _parse_page(self, html: str) -> list[dict]:
        """Parse a single Naukri search results page."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # Naukri uses article tags or div with specific classes for job cards
        job_cards = soup.find_all("div", class_=re.compile(r"srp-jobtuple|cust-job-tuple|jobTuple", re.I))

        # Fallback: try finding article elements
        if not job_cards:
            job_cards = soup.find_all("article", class_=re.compile(r"jobTuple|job-tuple", re.I))

        # Another fallback: look for the common job listing structure
        if not job_cards:
            job_cards = soup.select("div.list div.jobTupleHeader, div.srp-jobtuple-wrapper")

        if not job_cards:
            # Try the newer Naukri layout
            job_cards = soup.select("[data-job-id], .styles_jlc__main__VdwtF, .srp-jobtuple-wrapper")

        for card in job_cards:
            try:
                job = self._parse_card(card)
                if job and job.get("Company Name"):
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"[Naukri] Error parsing card: {e}")
                continue

        return jobs

    def _parse_card(self, card) -> dict | None:
        """Parse a single job card element."""
        # ── Job Title ──
        title_el = (
            card.find("a", class_=re.compile(r"title|jobTitle|desig", re.I))
            or card.find("a", attrs={"class": re.compile(r"title", re.I)})
            or card.select_one("a.title, a.job-title, .row1 a, .info-block a")
        )
        title = title_el.get_text(strip=True) if title_el else None

        # ── Job Link ──
        link = None
        if title_el and title_el.get("href"):
            link = title_el["href"]
            if link and not link.startswith("http"):
                link = "https://www.naukri.com" + link

        # ── Company Name ──
        company_el = (
            card.find("a", class_=re.compile(r"comp-name|company|subTitle", re.I))
            or card.find("span", class_=re.compile(r"comp-name|company", re.I))
            or card.select_one("a.comp-name, a.subTitle, .comp-dtl-header a, .companyInfo a")
        )
        company = company_el.get_text(strip=True) if company_el else None

        # ── Location ──
        loc_el = (
            card.find("span", class_=re.compile(r"loc-wrap|location|locWrap|ellipsis", re.I))
            or card.find("li", class_=re.compile(r"location|fleft", re.I))
            or card.select_one(".loc-wrap, .location, .locWrap span, .ni-job-tuple-icon-srp-location + span")
        )
        location_text = loc_el.get_text(strip=True) if loc_el else ""

        # ── Salary ──
        salary_el = (
            card.find("span", class_=re.compile(r"sal-wrap|salary|salWrap", re.I))
            or card.find("li", class_=re.compile(r"salary", re.I))
            or card.select_one(".sal-wrap, .salary, .ni-job-tuple-icon-srp-rupee + span")
        )
        salary = salary_el.get_text(strip=True) if salary_el else None
        if salary and salary.lower() in ["not disclosed", "not mentioned"]:
            salary = None

        # ── Date Posted ──
        date_el = (
            card.find("span", class_=re.compile(r"job-post-day|date|freshness", re.I))
            or card.select_one(".job-post-day, .freshness, .ni-job-tuple-icon-srp-calendar + span")
        )
        date_posted = date_el.get_text(strip=True) if date_el else ""

        if not title and not company:
            return None

        return self.make_job_record(
            company=company or "Unknown",
            title=title or "Data Analyst",
            location=location_text,
            platform=self.PLATFORM_NAME,
            date_posted=date_posted,
            salary=salary,
            link=link or "",
        )
