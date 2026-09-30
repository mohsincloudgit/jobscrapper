import httpx
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET
from typing import List
from app.scrapers.base import JobItem, parse_and_normalize_date

class WeWorkRemotelyScraper:
    SOURCE_NAME = "WeWorkRemotely"
    RSS_URL = "https://weworkremotely.com/remote-jobs.rss"

    async def scrape(self, keyword: str = "", location: str = "", max_results: int = 50) -> List[JobItem]:
        jobs: List[JobItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(self.RSS_URL, headers=headers)
                if resp.status_code != 200:
                    return jobs

                root = ET.fromstring(resp.content)
                items = root.findall(".//item")

                for item in items:
                    raw_title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else "https://weworkremotely.com"
                    pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    raw_desc = item.find("description").text if item.find("description") is not None else ""

                    # WWR titles are usually "Company Name: Job Title"
                    company = "WeWorkRemotely"
                    title = raw_title
                    if ":" in raw_title:
                        parts = raw_title.split(":", 1)
                        company = parts[0].strip()
                        title = parts[1].strip()

                    date_norm, date_rel = parse_and_normalize_date(pub_date)

                    clean_desc = ""
                    if raw_desc:
                        soup = BeautifulSoup(raw_desc, "html.parser")
                        clean_desc = " ".join(soup.get_text().split())[:200] + "..."

                    # Categories/Tags
                    tags = []
                    for cat in item.findall("category"):
                        if cat.text:
                            tags.append(cat.text.strip())

                    job = JobItem(
                        title=title,
                        company=company,
                        location="Anywhere (100% Remote)",
                        date_posted=date_norm,
                        date_relative=date_rel,
                        job_type="Full-Time Remote",
                        salary="Competitive / Unspecified",
                        source=self.SOURCE_NAME,
                        url=link,
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
            print(f"[WeWorkRemotely] Error scraping: {e}")

        return jobs
