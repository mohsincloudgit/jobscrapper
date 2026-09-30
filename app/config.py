import json
import os
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CREDENTIALS_DIR = BASE_DIR / "credentials"
SETTINGS_FILE = DATA_DIR / "settings.json"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CREDENTIALS_DIR, exist_ok=True)

class AppSettings(BaseModel):
    # Google Sheets Settings
    google_sync_enabled: bool = False
    sheets_mode: str = "webhook"  # "webhook" or "service_account"
    apps_script_url: str = ""
    spreadsheet_id: str = ""
    tab_name_prefix: str = "Jobs_"  # resulting tab: Jobs_2026-10-01
    date_format: str = "%Y-%m-%d"
    service_account_file: str = "credentials/service_account.json"
    
    # Scraper Defaults
    default_sources: List[str] = [
        "LinkedIn", "RemoteOK", "WeWorkRemotely", "Jobicy", 
        "Arbeitnow", "Remotive", "Reddit", "HackerNews"
    ]
    max_results_default: int = 50

def get_settings() -> AppSettings:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppSettings(**data)
        except Exception:
            pass
    settings = AppSettings()
    save_settings(settings)
    return settings

def save_settings(settings: AppSettings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings.model_dump(), f, indent=2)
