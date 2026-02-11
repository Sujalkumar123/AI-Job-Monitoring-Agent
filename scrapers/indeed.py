"""
Indeed India scraper for job listings.
Uses requests + BeautifulSoup to parse Indeed's search results.
"""

import re
import logging
from bs4 import BeautifulSoup

import config
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class IndeedScraper(BaseScraper):
    """Scraper for Indeed India job listings."""

    PLATFORM_NAME = "Indeed"

    def __init__(self):
        super().__init__()
        # Indeed-specific headers
        self.session.headers.update({
            "Referer": "https://in.indeed.com/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        })

    def scrape(self, role: str = None, location: str = None) -> list[dict]:
        """Scrape Data Analyst jobs from Indeed India."""
        role = role or config.SEARCH_ROLE
        location = location or config.SEARCH_LOCATION
        all_jobs = []

        for page in range(config.MAX_PAGES):
            url = config.get_indeed_url(role, page)
            resp = self._fetch(url)

            if not resp:
                logger.warning(f"[Indeed] Failed to fetch page {page + 1}")
                break

            jobs = self._parse_page(resp.text)
            if not jobs:
                logger.info(f"[Indeed] No jobs found on page {page + 1}, stopping pagination")
                break

            all_jobs.extend(jobs)
            logger.info(f"[Indeed] Page {page + 1}: found {len(jobs)} jobs")
            self._rate_limit()

        logger.info(f"[Indeed] Total jobs scraped: {len(all_jobs)}")
        return all_jobs

    def _parse_page(self, html: str) -> list[dict]:
        """Parse a single Indeed search results page."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # Indeed uses different structures — try multiple selectors
        job_cards = soup.find_all("div", class_=re.compile(r"job_seen_beacon|jobsearch-ResultsList|cardOutline|result", re.I))

        if not job_cards:
            job_cards = soup.select("div.job_seen_beacon, li.css-1ac2h1w, div.resultContent, td.resultContent")

        if not job_cards:
            # Fallback: look for the mosaic provider structure
            job_cards = soup.select("[data-jk], .tapItem, .job-seen-beacon")

        for card in job_cards:
            try:
                job = self._parse_card(card)
                if job and job.get("Company Name"):
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"[Indeed] Error parsing card: {e}")
                continue

        return jobs

    def _parse_card(self, card) -> dict | None:
        """Parse a single Indeed job card."""
        # ── Job Title ──
        title_el = (
            card.find("h2", class_=re.compile(r"jobTitle|title", re.I))
            or card.find("a", class_=re.compile(r"jcs-JobTitle", re.I))
            or card.select_one("h2.jobTitle a, a.jcs-JobTitle, .jobTitle > a, h2 a")
        )

        title = None
        link = None
        if title_el:
            # The title might be inside a span within the anchor
            title_span = title_el.find("span")
            title = title_span.get_text(strip=True) if title_span else title_el.get_text(strip=True)

            # Get link
            link_el = title_el if title_el.name == "a" else title_el.find("a")
            if link_el and link_el.get("href"):
                href = link_el["href"]
                if not href.startswith("http"):
                    link = f"https://in.indeed.com{href}"
                else:
                    link = href
            # Also try data-jk attribute for constructing link
            if not link:
                jk = card.get("data-jk") or (card.find(attrs={"data-jk": True}) or {}).get("data-jk")
                if jk:
                    link = f"https://in.indeed.com/viewjob?jk={jk}"

        # ── Company Name ──
        company_el = (
            card.find("span", attrs={"data-testid": "company-name"})
            or card.find("span", class_=re.compile(r"companyName|company", re.I))
            or card.select_one("[data-testid='company-name'], .companyName, .css-1h7lukg, .company")
        )
        company = company_el.get_text(strip=True) if company_el else None

        # ── Location ──
        loc_el = (
            card.find("div", attrs={"data-testid": "text-location"})
            or card.find("div", class_=re.compile(r"companyLocation|location", re.I))
            or card.select_one("[data-testid='text-location'], .companyLocation, .css-1restlb")
        )
        location_text = loc_el.get_text(strip=True) if loc_el else ""

        # ── Salary ──
        salary_el = (
            card.find("div", attrs={"data-testid": "attribute_snippet_testid"})
            or card.find("div", class_=re.compile(r"salary-snippet|salaryOnly", re.I))
            or card.select_one(".salary-snippet-container, .salaryOnly, .css-1ihavw2, [data-testid='attribute_snippet_testid']")
        )
        salary = None
        if salary_el:
            text = salary_el.get_text(strip=True)
            # Check if it looks like a salary (contains currency symbols or numbers)
            if any(c in text for c in ["₹", "INR", "lakh", "LPA", "per", "annum", ","]):
                salary = text

        # ── Date Posted ──
        date_el = (
            card.find("span", class_=re.compile(r"date|days", re.I))
            or card.select_one(".date, .css-qvloho, [data-testid='myJobsStateDate']")
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
