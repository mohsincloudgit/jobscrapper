import csv
import io
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from app.config import DATA_DIR

class CSVService:
    HEADERS = [
        "ID",
        "Job Title",
        "Company",
        "Location",
        "Date Posted",
        "Relative Age",
        "Job Type",
        "Salary / Compensation",
        "Source",
        "Job URL",
        "Tags",
        "Description Snippet",
        "Scraped At"
    ]

    @staticmethod
    def generate_csv_string(jobs: List[Dict[str, Any]]) -> str:
        """Generates a UTF-8 CSV string in-memory with BOM for Excel compatibility."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSVService.HEADERS)

        for j in jobs:
            tags_str = ", ".join(j.get("tags", [])) if isinstance(j.get("tags"), list) else str(j.get("tags", ""))
            writer.writerow([
                j.get("id", ""),
                j.get("title", ""),
                j.get("company", ""),
                j.get("location", ""),
                j.get("date_posted", ""),
                j.get("date_relative", ""),
                j.get("job_type", ""),
                j.get("salary", ""),
                j.get("source", ""),
                j.get("url", ""),
                tags_str,
                j.get("description_snippet", ""),
                j.get("scraped_at", "")
            ])

        return output.getvalue()

    @staticmethod
    def save_to_file(jobs: List[Dict[str, Any]], keyword: str = "") -> str:
        """Saves jobs to a CSV file in data/ directory and returns the filepath."""
        clean_kw = "".join(c for c in keyword if c.isalnum() or c in ("-", "_")).lower() or "all_jobs"
        now_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"jobs_{clean_kw}_{now_str}.csv"
        filepath = DATA_DIR / filename

        csv_content = CSVService.generate_csv_string(jobs)
        # Write with UTF-8 BOM so MS Excel displays Unicode characters cleanly
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            f.write(csv_content)

        return str(filepath)

    @staticmethod
    def list_saved_csvs() -> List[Dict[str, Any]]:
        """Returns metadata of all generated CSV files in data/."""
        files = []
        for p in DATA_DIR.glob("jobs_*.csv"):
            stat = p.stat()
            files.append({
                "filename": p.name,
                "size_kb": round(stat.st_size / 1024, 1),
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "path": str(p)
            })
        files.sort(key=lambda x: x["created_at"], reverse=True)
        return files
