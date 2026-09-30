import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field

class JobItem(BaseModel):
    id: str = ""
    title: str
    company: str
    location: str = "Remote"
    date_posted: str = ""        # Format: YYYY-MM-DD
    date_relative: str = ""      # e.g., "Today", "2 days ago"
    job_type: str = "Full-Time"  # Full-Time, Contract, etc.
    salary: str = "Not Specified"
    source: str                  # RemoteOK, WeWorkRemotely, Jobicy, Arbeitnow, Remotive
    url: str
    tags: List[str] = Field(default_factory=list)
    description_snippet: str = ""
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))

    def compute_id(self):
        raw = f"{self.source}_{self.company}_{self.title}_{self.url}"
        self.id = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
        return self.id


def parse_and_normalize_date(date_val) -> tuple[str, str]:
    """
    Given a date string or timestamp, normalizes to (YYYY-MM-DD, relative_str).
    """
    now = datetime.now(timezone.utc)
    target_dt = None

    if isinstance(date_val, (int, float)):
        # unix timestamp
        try:
            target_dt = datetime.fromtimestamp(date_val, tz=timezone.utc)
        except Exception:
            target_dt = now
    elif isinstance(date_val, str):
        date_str = date_val.strip()
        # Try various formats
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S GMT",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%d %b %Y",
            "%b %d, %Y"
        ]
        for fmt in formats:
            try:
                # Remove extra sub-seconds if present
                clean_str = date_str
                if "." in clean_str and ("T" in clean_str or " " in clean_str):
                    parts = clean_str.split(".")
                    suffix = parts[1]
                    # keep timezone if present
                    if "+" in suffix:
                        clean_str = parts[0] + "+" + suffix.split("+")[1]
                    elif "-" in suffix and len(suffix.split("-")[1]) <= 5:
                        clean_str = parts[0] + "-" + suffix.split("-")[1]
                    elif "Z" in suffix:
                        clean_str = parts[0] + "Z"
                    else:
                        clean_str = parts[0]
                target_dt = datetime.strptime(clean_str, fmt)
                if target_dt.tzinfo is None:
                    target_dt = target_dt.replace(tzinfo=timezone.utc)
                break
            except Exception:
                continue

    if not target_dt:
        target_dt = now

    date_formatted = target_dt.strftime("%Y-%m-%d")
    
    # Calculate relative string
    diff = now.date() - target_dt.date()
    days = diff.days

    if days <= 0:
        relative = "Today"
    elif days == 1:
        relative = "Yesterday"
    elif days < 7:
        relative = f"{days}d ago"
    elif days < 30:
        weeks = days // 7
        relative = f"{weeks}w ago" if weeks > 1 else "1w ago"
    else:
        months = days // 30
        relative = f"{months}mo ago" if months > 1 else "1mo ago"

    return date_formatted, relative
