import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from app.scrapers.base import JobItem
from app.scrapers.remoteok import RemoteOKScraper
from app.scrapers.jobicy import JobicyScraper
from app.scrapers.arbeitnow import ArbeitnowScraper
from app.scrapers.remotive import RemotiveScraper
from app.scrapers.weworkremotely import WeWorkRemotelyScraper
from app.scrapers.linkedin import LinkedInScraper
from app.scrapers.reddit import RedditScraper
from app.scrapers.hackernews import HackerNewsScraper

SCRAPERS = {
    "LinkedIn": LinkedInScraper(),
    "RemoteOK": RemoteOKScraper(),
    "WeWorkRemotely": WeWorkRemotelyScraper(),
    "Jobicy": JobicyScraper(),
    "Arbeitnow": ArbeitnowScraper(),
    "Remotive": RemotiveScraper(),
    "Reddit": RedditScraper(),
    "HackerNews": HackerNewsScraper(),
}

SOURCE_METADATA = {
    "LinkedIn": {"category": "professional", "badge": "#0a66c2", "type": "Professional Network"},
    "RemoteOK": {"category": "job_boards", "badge": "#ff4742", "type": "Tech Job Board"},
    "WeWorkRemotely": {"category": "job_boards", "badge": "#e24a4a", "type": "Remote Job Board"},
    "Jobicy": {"category": "job_boards", "badge": "#2563eb", "type": "Global Remote Board"},
    "Arbeitnow": {"category": "job_boards", "badge": "#059669", "type": "European & Remote"},
    "Remotive": {"category": "job_boards", "badge": "#8b5cf6", "type": "Handpicked Tech"},
    "Reddit": {"category": "social", "badge": "#ff4500", "type": "Social Media (r/forhire)"},
    "HackerNews": {"category": "social", "badge": "#ff6600", "type": "Tech Community & Startups"},
}

class JobAggregator:
    def __init__(self):
        self.scrapers = SCRAPERS

    async def scrape_all(
        self,
        keyword: str = "",
        location: str = "",
        category: str = "all",
        sources: Optional[List[str]] = None,
        date_filter: str = "all",
        max_results: int = 100
    ) -> Dict[str, Any]:
        if not sources:
            sources = list(self.scrapers.keys())

        # Determine effective query keywords if category is selected
        effective_kw = keyword.strip()
        if category and category.lower() != "all":
            category_keywords = {
                "engineering": "developer engineer",
                "data_ai": "data ai machine learning",
                "design": "designer ui ux",
                "marketing": "marketing sales seo",
                "devops": "devops cloud infrastructure sre",
                "product": "product manager agile"
            }
            extra = category_keywords.get(category.lower(), "")
            if extra and not effective_kw:
                effective_kw = extra

        tasks = []
        active_sources = []
        per_source_limit = max(15, max_results // max(1, len(sources)) + 10)

        for src_name in sources:
            scraper = self.scrapers.get(src_name)
            if scraper:
                active_sources.append(src_name)
                tasks.append(scraper.scrape(keyword=effective_kw, location=location, max_results=per_source_limit))

        results_by_source = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs: List[JobItem] = []
        source_counts: Dict[str, int] = {}

        for src_name, result in zip(active_sources, results_by_source):
            if isinstance(result, list):
                source_counts[src_name] = len(result)
                all_jobs.extend(result)
            else:
                source_counts[src_name] = 0
                print(f"[Aggregator] Error from {src_name}: {result}")

        # Deduplicate jobs by URL and by company+title
        unique_jobs: List[JobItem] = []
        seen_urls = set()
        seen_titles = set()

        for j in all_jobs:
            norm_url = j.url.lower().split("?")[0].rstrip("/")
            title_key = f"{j.company.lower().strip()}_{j.title.lower().strip()}"
            if norm_url in seen_urls or title_key in seen_titles:
                continue
            seen_urls.add(norm_url)
            seen_titles.add(title_key)
            unique_jobs.append(j)

        # Apply Date Filter
        now = datetime.now(timezone.utc).date()
        filtered_jobs = []

        for j in unique_jobs:
            try:
                j_date = datetime.strptime(j.date_posted, "%Y-%m-%d").date()
                diff_days = (now - j_date).days
            except Exception:
                diff_days = 999

            if date_filter == "today" and diff_days > 0:
                continue
            elif date_filter == "3days" and diff_days > 3:
                continue
            elif date_filter == "7days" and diff_days > 7:
                continue
            elif date_filter == "14days" and diff_days > 14:
                continue
            elif date_filter == "30days" and diff_days > 30:
                continue

            filtered_jobs.append(j)

        # Sort: newest date_posted first
        def sort_key(item: JobItem):
            try:
                return datetime.strptime(item.date_posted, "%Y-%m-%d")
            except Exception:
                return datetime.min.replace(tzinfo=timezone.utc)

        filtered_jobs.sort(key=sort_key, reverse=True)

        # Slice to max_results
        final_jobs = filtered_jobs[:max_results]

        # Calculate statistics
        today_str = now.strftime("%Y-%m-%d")
        today_count = sum(1 for j in final_jobs if j.date_posted == today_str or j.date_relative == "Today")

        return {
            "total_found": len(final_jobs),
            "today_jobs_count": today_count,
            "sources_queried": active_sources,
            "source_counts": source_counts,
            "query": {
                "keyword": keyword,
                "location": location,
                "category": category,
                "date_filter": date_filter,
                "max_results": max_results
            },
            "jobs": [j.model_dump() for j in final_jobs]
        }
