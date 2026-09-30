import httpx
from bs4 import BeautifulSoup
from typing import List
from app.scrapers.base import JobItem, parse_and_normalize_date

class JobicyScraper:
    SOURCE_NAME = "Jobicy"
    BASE_URL = "https://jobicy.com/api/v2/remote-jobs"

    async def scrape(self, keyword: str = "", location: str = "", max_results: int = 50) -> List[JobItem]:
        jobs: List[JobItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        params = {"count": min(max_results * 2, 100)}
        if keyword:
            params["tag"] = keyword.strip()
        if location and location.lower() != "any":
            params["geo"] = location.strip()

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(self.BASE_URL, params=params, headers=headers)
                if resp.status_code != 200:
                    return jobs
                
                data = resp.json()
                items = data.get("jobs", [])
                for item in items:
                    title = item.get("jobTitle", "").strip()
                    company = item.get("companyName", "").strip()
                    loc = item.get("jobGeo", "").strip() or "Remote"
                    raw_date = item.get("pubDate")
                    date_norm, date_rel = parse_and_normalize_date(raw_date)
                    
                    job_type = item.get("jobType", "Full-Time")
                    if isinstance(job_type, list):
                        job_type = ", ".join(job_type)
                    
                    # Salary
                    sal_min = item.get("annualSalaryMin")
                    sal_max = item.get("annualSalaryMax")
                    curr = item.get("salaryCurrency", "USD")
                    if sal_min and sal_max:
                        salary = f"{sal_min} - {sal_max} {curr}"
                    elif sal_min:
                        salary = f"From {sal_min} {curr}"
                    elif sal_max:
                        salary = f"Up to {sal_max} {curr}"
                    else:
                        salary = "Competitive / Unspecified"

                    # Description snippet
                    raw_desc = item.get("jobExcerpt") or item.get("jobDescription", "")
                    clean_desc = ""
                    if raw_desc:
                        soup = BeautifulSoup(raw_desc, "html.parser")
                        clean_desc = " ".join(soup.get_text().split())[:200] + "..."

                    tags = []
                    industry = item.get("jobIndustry", "")
                    if industry:
                        if isinstance(industry, list):
                            tags.extend(industry)
                        else:
                            tags.append(str(industry))

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

                    if keyword:
                        kw = keyword.lower()
                        text_to_check = f"{title} {company} {' '.join(tags)} {clean_desc}".lower()
                        if kw not in text_to_check:
                            continue

                    jobs.append(job)
                    if len(jobs) >= max_results:
                        break

        except Exception as e:
            print(f"[Jobicy] Error scraping: {e}")

        return jobs
