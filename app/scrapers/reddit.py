import httpx
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from typing import List
from app.scrapers.base import JobItem, parse_and_normalize_date

class RedditScraper:
    SOURCE_NAME = "Reddit"
    RSS_URL = "https://www.reddit.com/r/forhire/new/.rss"

    async def scrape(self, keyword: str = "", location: str = "", max_results: int = 25) -> List[JobItem]:
        jobs: List[JobItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(self.RSS_URL, headers=headers)
                if resp.status_code != 200:
                    return jobs

                root = ET.fromstring(resp.content)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", ns)

                for e in entries:
                    title_elem = e.find("atom:title", ns)
                    link_elem = e.find("atom:link", ns)
                    updated_elem = e.find("atom:updated", ns)
                    content_elem = e.find("atom:content", ns)
                    author_elem = e.find("atom:author/atom:name", ns)

                    raw_title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    # We only care about [Hiring] posts on social media
                    if not raw_title.lower().startswith("[hiring]") and "hiring" not in raw_title.lower()[:15]:
                        continue

                    clean_title = raw_title.replace("[Hiring]", "").replace("[hiring]", "").strip()
                    author = author_elem.text.strip() if author_elem is not None and author_elem.text else "Reddit Client"
                    job_url = link_elem.get("href", "") if link_elem is not None else ""
                    updated_date = updated_elem.text.strip() if updated_elem is not None and updated_elem.text else ""
                    date_norm, date_rel = parse_and_normalize_date(updated_date)

                    clean_desc = ""
                    if content_elem is not None and content_elem.text:
                        soup = BeautifulSoup(content_elem.text, "html.parser")
                        clean_desc = " ".join(soup.get_text().split())[:220] + "..."

                    # Check keyword
                    if keyword:
                        words = [w.strip().lower() for w in keyword.split() if len(w.strip()) > 1]
                        haystack = f"{clean_title} {clean_desc}".lower()
                        # If any significant query word is found
                        if words and not any(w in haystack for w in words):
                            continue

                    job = JobItem(
                        title=clean_title,
                        company=f"u/{author} (r/forhire)",
                        location="Remote / Freelance",
                        date_posted=date_norm,
                        date_relative=date_rel,
                        job_type="Freelance / Contract",
                        salary="See Reddit Thread",
                        source=self.SOURCE_NAME,
                        url=job_url,
                        tags=["Social Media", "Reddit", "Direct Hiring"],
                        description_snippet=clean_desc
                    )
                    job.compute_id()

                    jobs.append(job)
                    if len(jobs) >= max_results:
                        break

        except Exception as e:
            print(f"[Reddit] Error scraping: {e}")

        return jobs
