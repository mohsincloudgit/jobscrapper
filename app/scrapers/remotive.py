import httpx
from bs4 import BeautifulSoup
from typing import List
from app.scrapers.base import JobItem, parse_and_normalize_date

class RemotiveScraper:
    SOURCE_NAME = "Remotive"
    BASE_URL = "https://remotive.com/api/remote-jobs"

    async def scrape(self, keyword: str = "", location: str = "", max_results: int = 50) -> List[JobItem]:
        jobs: List[JobItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        params = {"limit": min(max_results * 2, 100)}
        if keyword:
            params["search"] = keyword.strip()

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(self.BASE_URL, params=params, headers=headers)
                if resp.status_code != 200:
                    return jobs

                data = resp.json().get("jobs", [])
                for item in data:
                    title = item.get("title", "").strip()
                    company = item.get("company_name", "").strip()
                    loc = item.get("candidate_required_location", "").strip() or "Worldwide / Remote"
                    raw_date = item.get("publication_date")
                    date_norm, date_rel = parse_and_normalize_date(raw_date)

                    job_type = item.get("job_type", "full_time").replace("_", " ").title()
                    salary = item.get("salary", "").strip() or "Competitive / Unspecified"
                    tags = item.get("tags", [])
                    if not isinstance(tags, list):
                        tags = []

                    raw_desc = item.get("description", "")
                    clean_desc = ""
                    if raw_desc:
                        soup = BeautifulSoup(raw_desc, "html.parser")
                        clean_desc = " ".join(soup.get_text().split())[:200] + "..."

                    job = JobItem(
                        title=title,
                        company=company,
                        location=loc,
                        date_posted=date_norm,
                        date_relative=date_rel,
                        job_type=job_type,
                        salary=salary,
                        source=self.SOURCE_NAME,
                        url=item.get("url", ""),
                        tags=tags[:5],
                        description_snippet=clean_desc
                    )
                    job.compute_id()

                    if location and location.lower() != "any":
                        loc_kw = location.lower()
                        if loc_kw not in loc.lower() and "remote" not in loc.lower() and "worldwide" not in loc.lower():
                            continue

                    jobs.append(job)
                    if len(jobs) >= max_results:
                        break

        except Exception as e:
            print(f"[Remotive] Error scraping: {e}")

        return jobs
