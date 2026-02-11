"""Job scraper modules for multiple platforms."""

from .naukri import NaukriScraper
from .indeed import IndeedScraper
from .linkedin import LinkedInScraper
from .wellfound import WellfoundScraper

__all__ = ["NaukriScraper", "IndeedScraper", "LinkedInScraper", "WellfoundScraper"]
