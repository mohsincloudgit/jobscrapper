import httpx
from bs4 import BeautifulSoup
from typing import List
from app.scrapers.base import JobItem, parse_and_normalize_date

class RemoteOKScraper:
    SOURCE_NAME = "RemoteOK"
    BASE_URL = "https://remoteok.com/api"

    async def scrape(self, keyword: str = "", location: str = "", max_results: int = 50) -> List[JobItem]:
        jobs: List[JobItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        url = self.BASE_URL
        if keyword:
            clean_tag = keyword.strip().lower().replace(" ", "-")
            url = f"{self.BASE_URL}?tag={clean_tag}"

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return jobs
                
                data = resp.json()
                for item in data:
                    if not isinstance(item, dict) or "position" not in item:
                        continue
                    
                    title = item.get("position", "").strip()
                    company = item.get("company", "").strip()
                    loc = item.get("location", "").strip() or "Remote"
                    raw_date = item.get("date")
                    date_norm, date_rel = parse_and_normalize_date(raw_date)
                    tags = item.get("tags", [])
                    if isinstance(tags, list):
                        tags = [str(t).strip() for t in tags if str(t).strip()]
                    else:
                        tags = []

                    # Salary parsing
                    sal_min = item.get("salary_min")
                    sal_max = item.get("salary_max")
                    if sal_min and sal_max:
                        salary = f"${sal_min:,.0f} - ${sal_max:,.0f} USD"
                    elif sal_min:
                        salary = f"From ${sal_min:,.0f} USD"
                    elif sal_max:
                        salary = f"Up to ${sal_max:,.0f} USD"
                    else:
                        salary = "Competitive / Unspecified"

                    # Description snippet
                    raw_desc = item.get("description", "")
                    clean_desc = ""
                    if raw_desc:
                        soup = BeautifulSoup(raw_desc, "html.parser")
                        clean_desc = " ".join(soup.get_text().split())[:200] + "..."

                    job_url = item.get("url", "")
                    if job_url and not job_url.startswith("http"):
                        job_url = f"https://remoteok.com{job_url}"

                    job = JobItem(
                        title=title,
                        company=company,
                        location=loc,
                        date_posted=date_norm,
                        date_relative=date_rel,
                        job_type="Full-Time Remote",
                        salary=salary,
                        source=self.SOURCE_NAME,
                        url=job_url or "https://remoteok.com",
                        tags=tags[:6],
                        description_snippet=clean_desc
                    )
                    job.compute_id()

                    # Filtering by keyword/location if query param didn't filter
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
            print(f"[RemoteOK] Error scraping: {e}")

        return jobs
