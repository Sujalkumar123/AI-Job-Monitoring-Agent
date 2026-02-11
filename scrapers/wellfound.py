"""
Wellfound (formerly AngelList) scraper for job listings.
Scrapes Wellfound's public job search pages.
"""

import re
import json
import logging
from bs4 import BeautifulSoup

import config
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class WellfoundScraper(BaseScraper):
    """Scraper for Wellfound job listings."""

    PLATFORM_NAME = "Wellfound"

    def __init__(self):
        super().__init__()
        self.session.headers.update({
            "Referer": "https://wellfound.com/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
        })

    def scrape(self, role: str = None, location: str = None) -> list[dict]:
        """Scrape Data Analyst jobs from Wellfound."""
        role = role or config.SEARCH_ROLE
        location = location or config.SEARCH_LOCATION
        all_jobs = []

        # Try multiple URL formats
        urls = [
            config.get_wellfound_url(role),
            f"https://wellfound.com/jobs?role={role.replace(' ', '+')}+Entry+Level&location={location.replace(' ', '+')}",
            f"https://wellfound.com/role/data-analyst",
        ]

        for url in urls:
            resp = self._fetch(url)
            if not resp:
                logger.warning(f"[Wellfound] Failed to fetch: {url}")
                continue

            # Try parsing Apollo state (JSON embedded in page)
            apollo_jobs = self._parse_apollo_state(resp.text)
            if apollo_jobs:
                all_jobs.extend(apollo_jobs)
                logger.info(f"[Wellfound] Found {len(apollo_jobs)} jobs via Apollo state")
                break

            # Fallback: parse HTML directly
            html_jobs = self._parse_html(resp.text)
            if html_jobs:
                all_jobs.extend(html_jobs)
                logger.info(f"[Wellfound] Found {len(html_jobs)} jobs via HTML parsing")
                break

            self._rate_limit()

        # Filter for India-based jobs
        india_jobs = self._filter_india(all_jobs, location)
        logger.info(f"[Wellfound] Total India jobs: {len(india_jobs)}")
        return india_jobs

    def _parse_apollo_state(self, html: str) -> list[dict]:
        """Try to extract job data from Wellfound's Apollo/Next.js state."""
        jobs = []
        try:
            soup = BeautifulSoup(html, "lxml")

            # Look for __NEXT_DATA__ or __APOLLO_STATE__
            script_tags = soup.find_all("script", id="__NEXT_DATA__")
            if not script_tags:
                script_tags = soup.find_all("script", string=re.compile(r"__APOLLO_STATE__|window\.__NEXT_DATA__"))

            for script in script_tags:
                try:
                    text = script.string or script.get_text()
                    # Extract JSON
                    if "__NEXT_DATA__" in str(script.get("id", "")):
                        data = json.loads(text)
                    else:
                        match = re.search(r'({.+})', text, re.DOTALL)
                        if match:
                            data = json.loads(match.group(1))
                        else:
                            continue

                    # Recursively search for job listings in the JSON
                    self._extract_jobs_from_json(data, jobs)
                except (json.JSONDecodeError, Exception) as e:
                    logger.debug(f"[Wellfound] JSON parse error: {e}")
                    continue

        except Exception as e:
            logger.debug(f"[Wellfound] Apollo state parsing failed: {e}")

        return jobs

    def _extract_jobs_from_json(self, data, jobs: list, depth: int = 0):
        """Recursively extract job objects from nested JSON."""
        if depth > 15:
            return

        if isinstance(data, dict):
            # Check if this looks like a job listing
            if self._is_job_object(data):
                job = self._json_to_job(data)
                if job:
                    jobs.append(job)

            for value in data.values():
                self._extract_jobs_from_json(value, jobs, depth + 1)

        elif isinstance(data, list):
            for item in data:
                self._extract_jobs_from_json(item, jobs, depth + 1)

    def _is_job_object(self, obj: dict) -> bool:
        """Check if a dict looks like a job listing."""
        job_keys = {"title", "name", "jobTitle", "role"}
        company_keys = {"company", "companyName", "startup", "organization"}
        return bool(job_keys & set(obj.keys())) and bool(company_keys & set(obj.keys()) or "company" in str(obj).lower())

    def _json_to_job(self, obj: dict) -> dict | None:
        """Convert a JSON job object to our standard format."""
        title = obj.get("title") or obj.get("jobTitle") or obj.get("name") or obj.get("role", "")
        company = (
            obj.get("companyName") or
            obj.get("company", {}).get("name", "") if isinstance(obj.get("company"), dict) else
            obj.get("company", "")
        )
        location_val = obj.get("location") or obj.get("locationNames", "") or ""
        if isinstance(location_val, list):
            location_val = ", ".join(location_val)

        salary = None
        if obj.get("compensation"):
            salary = str(obj["compensation"])
        elif obj.get("salary"):
            salary = str(obj["salary"])
        elif obj.get("salaryRange"):
            salary = str(obj["salaryRange"])

        link = obj.get("url") or obj.get("slug", "")
        if link and not link.startswith("http"):
            link = f"https://wellfound.com{link}" if link.startswith("/") else f"https://wellfound.com/jobs/{link}"

        date_posted = obj.get("postedAt") or obj.get("liveStartAt") or obj.get("createdAt", "")

        if not company and not title:
            return None

        return self.make_job_record(
            company=str(company).strip() if company else "Unknown",
            title=str(title).strip() if title else "Data Analyst",
            location=str(location_val).strip(),
            platform=self.PLATFORM_NAME,
            date_posted=str(date_posted),
            salary=salary,
            link=link or "",
        )

    def _parse_html(self, html: str) -> list[dict]:
        """Fallback HTML parsing for Wellfound job listings."""
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # Try various selectors for Wellfound's different layouts
        job_cards = soup.select(
            "[data-test='JobListing'], "
            ".styles_component__nv7Bj, "
            ".styles_jobCard___hKKm, "
            "div[class*='jobListing'], "
            "div[class*='JobCard'], "
            "div[class*='job-listing']"
        )

        if not job_cards:
            # Try broader selectors
            job_cards = soup.find_all("div", class_=re.compile(r"job|listing|posting", re.I))

        for card in job_cards:
            try:
                # Title
                title_el = card.find(["h2", "h3", "a"], class_=re.compile(r"title|name|role", re.I))
                title = title_el.get_text(strip=True) if title_el else None

                # Company
                company_el = card.find(["a", "span", "h3"], class_=re.compile(r"company|startup|org", re.I))
                company = company_el.get_text(strip=True) if company_el else None

                # Location
                loc_el = card.find(["span", "div"], class_=re.compile(r"location|loc", re.I))
                loc = loc_el.get_text(strip=True) if loc_el else ""

                # Salary
                sal_el = card.find(["span", "div"], class_=re.compile(r"salary|compensation|pay", re.I))
                salary = sal_el.get_text(strip=True) if sal_el else None

                # Link
                link_el = card.find("a", href=True)
                link = link_el["href"] if link_el else ""
                if link and not link.startswith("http"):
                    link = f"https://wellfound.com{link}"

                if not title and not company:
                    continue

                jobs.append(self.make_job_record(
                    company=company or "Unknown",
                    title=title or "Data Analyst",
                    location=loc,
                    platform=self.PLATFORM_NAME,
                    date_posted="",
                    salary=salary,
                    link=link,
                ))
            except Exception as e:
                logger.debug(f"[Wellfound] Error parsing HTML card: {e}")
                continue

        return jobs

    def _filter_india(self, jobs: list[dict], location: str) -> list[dict]:
        """Filter jobs to only include India-based positions."""
        india_keywords = [
            "india", "bangalore", "bengaluru", "mumbai", "delhi",
            "hyderabad", "pune", "chennai", "kolkata", "gurgaon",
            "gurugram", "noida", "ahmedabad", "jaipur", "kochi",
            "thiruvananthapuram", "lucknow", "chandigarh", "indore",
            "coimbatore", "nagpur", "visakhapatnam", "surat", "remote, india",
        ]

        filtered = []
        for job in jobs:
            loc = job.get("Location", "").lower()
            if any(keyword in loc for keyword in india_keywords) or not loc:
                filtered.append(job)

        return filtered
