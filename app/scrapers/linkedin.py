import httpx
from bs4 import BeautifulSoup
from typing import List
from app.scrapers.base import JobItem, parse_and_normalize_date

class LinkedInScraper:
    SOURCE_NAME = "LinkedIn"
    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    async def scrape(self, keyword: str = "", location: str = "", max_results: int = 25) -> List[JobItem]:
        jobs: List[JobItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        search_kw = keyword.strip() or "software"
        search_loc = location.strip() if location and location.lower() != "any" else "Remote"

        params = {
            "keywords": search_kw,
            "location": search_loc,
            "start": 0
        }

        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                resp = await client.get(self.BASE_URL, params=params, headers=headers)
                if resp.status_code != 200:
                    return jobs

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.find_all("li")

                for card in cards:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    loc_elem = card.find("span", class_="job-search-card__location")
                    date_elem = card.find("time")
                    link_elem = card.find("a", class_="base-card__full-link") or card.find("a")

                    if not title_elem:
                        continue

                    title = title_elem.text.strip()
                    company = company_elem.text.strip() if company_elem else "Company on LinkedIn"
                    loc = loc_elem.text.strip() if loc_elem else search_loc
                    
                    raw_date = date_elem.get("datetime") if date_elem else ""
                    if not raw_date and date_elem:
                        raw_date = date_elem.text.strip()
                    date_norm, date_rel = parse_and_normalize_date(raw_date)

                    job_url = link_elem.get("href", "") if link_elem else ""
                    if job_url and "?" in job_url:
                        job_url = job_url.split("?")[0]  # clean tracking params

                    job = JobItem(
                        title=title,
                        company=company,
                        location=loc,
                        date_posted=date_norm,
                        date_relative=date_rel,
                        job_type="Full-Time / Direct",
                        salary="See LinkedIn Listing",
                        source=self.SOURCE_NAME,
                        url=job_url or "https://www.linkedin.com/jobs",
                        tags=["LinkedIn", "Professional Network"],
                        description_snippet=f"Verified LinkedIn Job Posting by {company} in {loc}."
                    )
                    job.compute_id()

                    jobs.append(job)
                    if len(jobs) >= max_results:
                        break

        except Exception as e:
            print(f"[LinkedIn] Error scraping: {e}")

        return jobs
