import httpx
from bs4 import BeautifulSoup
from typing import List
from app.scrapers.base import JobItem, parse_and_normalize_date

class HackerNewsScraper:
    SOURCE_NAME = "HackerNews"
    BASE_URL = "https://hn.algolia.com/api/v1/search_by_date"

    async def scrape(self, keyword: str = "", location: str = "", max_results: int = 25) -> List[JobItem]:
        jobs: List[JobItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        search_query = f"{keyword.strip()} hiring" if keyword.strip() else "who is hiring"

        params = {
            "query": search_query,
            "tags": "comment",
            "hitsPerPage": min(max_results * 2, 40)
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(self.BASE_URL, params=params, headers=headers)
                if resp.status_code != 200:
                    return jobs

                hits = resp.json().get("hits", [])
                for h in hits:
                    raw_text = h.get("comment_text", "")
                    if not raw_text:
                        continue

                    soup = BeautifulSoup(raw_text, "html.parser")
                    clean_text = " ".join(soup.get_text().split())
                    if not clean_text:
                        continue

                    # Often first line or 60 chars is company | role | location
                    lines = [ln.strip() for ln in soup.get_text().splitlines() if ln.strip()]
                    first_line = lines[0] if lines else clean_text[:80]

                    company = h.get("author", "Tech Startup")
                    title = first_line[:100]
                    if "|" in first_line:
                        parts = first_line.split("|")
                        company = parts[0].strip()
                        title = " | ".join(parts[1:3]).strip()

                    date_posted = h.get("created_at", "")
                    date_norm, date_rel = parse_and_normalize_date(date_posted)

                    obj_id = h.get("objectID", "")
                    job_url = f"https://news.ycombinator.com/item?id={obj_id}"

                    job = JobItem(
                        title=title or f"Hiring Post on YC HackerNews by {company}",
                        company=company,
                        location="Remote / Hybrid (YC Community)",
                        date_posted=date_norm,
                        date_relative=date_rel,
                        job_type="Full-Time / Startup",
                        salary="Competitive / Equity",
                        source=self.SOURCE_NAME,
                        url=job_url,
                        tags=["Community", "HackerNews", "YC Startups"],
                        description_snippet=clean_text[:220] + "..."
                    )
                    job.compute_id()

                    jobs.append(job)
                    if len(jobs) >= max_results:
                        break

        except Exception as e:
            print(f"[HackerNews] Error scraping: {e}")

        return jobs
