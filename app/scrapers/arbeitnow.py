import httpx
from bs4 import BeautifulSoup
from typing import List
from app.scrapers.base import JobItem, parse_and_normalize_date

class ArbeitnowScraper:
    SOURCE_NAME = "Arbeitnow"
    BASE_URL = "https://www.arbeitnow.com/api/job-board-api"

    async def scrape(self, keyword: str = "", location: str = "", max_results: int = 50) -> List[JobItem]:
        jobs: List[JobItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(self.BASE_URL, headers=headers)
                if resp.status_code != 200:
                    return jobs
                
                data = resp.json().get("data", [])
                for item in data:
                    title = item.get("title", "").strip()
                    company = item.get("company_name", "").strip()
                    loc = item.get("location", "").strip() or "Remote"
                    is_remote = item.get("remote", False)
                    if is_remote and "remote" not in loc.lower():
                        loc = f"{loc} (Remote)"
                        
                    raw_date = item.get("created_at")
                    date_norm, date_rel = parse_and_normalize_date(raw_date)

                    job_types = item.get("job_types", ["Full-Time"])
                    job_type_str = ", ".join(job_types) if isinstance(job_types, list) else str(job_types)

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
                        job_type=job_type_str or "Full-Time",
                        salary="Competitive / Unspecified",
                        source=self.SOURCE_NAME,
                        url=item.get("url", ""),
                        tags=tags[:5],
                        description_snippet=clean_desc
                    )
                    job.compute_id()

                    if keyword:
                        kw = keyword.lower()
                        text_to_check = f"{title} {company} {' '.join(tags)} {clean_desc}".lower()
                        if kw not in text_to_check:
                            continue

                    if location and location.lower() != "any":
                        loc_kw = location.lower()
                        if loc_kw not in loc.lower() and "remote" not in loc.lower() and loc_kw != "remote":
                            continue

                    jobs.append(job)
                    if len(jobs) >= max_results:
                        break

        except Exception as e:
            print(f"[Arbeitnow] Error scraping: {e}")

        return jobs
