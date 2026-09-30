from app.scrapers.base import JobItem
from app.scrapers.aggregator import JobAggregator
from app.scrapers.linkedin import LinkedInScraper
from app.scrapers.reddit import RedditScraper
from app.scrapers.hackernews import HackerNewsScraper
from app.scrapers.remoteok import RemoteOKScraper
from app.scrapers.weworkremotely import WeWorkRemotelyScraper
from app.scrapers.jobicy import JobicyScraper
from app.scrapers.arbeitnow import ArbeitnowScraper
from app.scrapers.remotive import RemotiveScraper

__all__ = [
    "JobItem",
    "JobAggregator",
    "LinkedInScraper",
    "RedditScraper",
    "HackerNewsScraper",
    "RemoteOKScraper",
    "WeWorkRemotelyScraper",
    "JobicyScraper",
    "ArbeitnowScraper",
    "RemotiveScraper"
]
