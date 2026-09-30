import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Response, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from app.config import get_settings, save_settings, AppSettings, DATA_DIR, BASE_DIR, CREDENTIALS_DIR
from app.scrapers.aggregator import JobAggregator
from app.services.csv_service import CSVService
from app.services.sheets_service import GoogleSheetsService

app = FastAPI(
    title="Universal Job Scraper & Sheet Automator",
    description="Multi-source job scraper with CSV export and automated date-wise Google Sheets sync",
    version="1.0.0"
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

aggregator = JobAggregator()

class ScrapeRequest(BaseModel):
    keyword: str = ""
    location: str = "Any"
    category: str = "all"
    sources: List[str] = [
        "LinkedIn", "RemoteOK", "WeWorkRemotely", "Jobicy", 
        "Arbeitnow", "Remotive", "Reddit", "HackerNews"
    ]
    date_filter: str = "all" # "all", "today", "3days", "7days", "14days", "30days"
    max_results: int = 50
    auto_sync_sheets: bool = False

class ExportCsvRequest(BaseModel):
    jobs: List[Dict[str, Any]]
    keyword: str = "jobs"

class SheetsSyncRequest(BaseModel):
    jobs: List[Dict[str, Any]]
    tab_name: Optional[str] = ""

class TestSheetsRequest(BaseModel):
    webhook_url: Optional[str] = ""

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Job Scraper is Initializing...</h1>", status_code=200)
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/api/scrape")
async def handle_scrape(req: ScrapeRequest):
    try:
        # Run multi-source scraping
        result = await aggregator.scrape_all(
            keyword=req.keyword,
            location=req.location,
            category=req.category,
            sources=req.sources,
            date_filter=req.date_filter,
            max_results=req.max_results
        )

        jobs = result.get("jobs", [])
        
        # Save to CSV automatically
        csv_path = CSVService.save_to_file(jobs, keyword=req.keyword)
        csv_filename = Path(csv_path).name

        # Google Sheets Sync if enabled
        sheets_sync_result = None
        settings = get_settings()
        if req.auto_sync_sheets or settings.google_sync_enabled:
            sheets_sync_result = await GoogleSheetsService.sync_jobs(jobs)

        return {
            "status": "success",
            "data": result,
            "csv_filename": csv_filename,
            "sheets_sync": sheets_sync_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/csv")
async def export_csv(req: ExportCsvRequest):
    try:
        csv_data = CSVService.generate_csv_string(req.jobs)
        clean_kw = "".join(c for c in req.keyword if c.isalnum() or c in ("-", "_")).lower() or "jobs"
        filename = f"{clean_kw}_export.csv"
        
        return Response(
            content=csv_data.encode("utf-8-sig"),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
async def download_csv_file(filename: str):
    file_path = DATA_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="text/csv"
    )

@app.get("/api/history")
async def get_history():
    files = CSVService.list_saved_csvs()
    return {"history": files}

@app.post("/api/sheets/sync")
async def manual_sheets_sync(req: SheetsSyncRequest):
    if not req.jobs:
        raise HTTPException(status_code=400, detail="No jobs provided to sync")
    res = await GoogleSheetsService.sync_jobs(req.jobs, tab_name=req.tab_name or "")
    return res

@app.get("/api/sheets/script-code")
async def get_apps_script_code():
    code = GoogleSheetsService.get_apps_script_code()
    return {"script_code": code}

@app.get("/api/settings")
async def get_app_settings():
    settings = get_settings()
    data = settings.model_dump()
    # Check if service account file exists
    sa_exists = (BASE_DIR / settings.service_account_file).exists()
    data["service_account_exists"] = sa_exists
    return data

@app.post("/api/settings")
async def update_app_settings(new_settings: AppSettings):
    save_settings(new_settings)
    return {"status": "success", "settings": new_settings.model_dump()}

@app.post("/api/settings/test-sheets")
async def test_sheets_connection(req: TestSheetsRequest):
    url = req.webhook_url
    if not url:
        settings = get_settings()
        url = settings.apps_script_url
    if not url:
        return {"success": False, "error": "No Webhook URL specified"}
    return await GoogleSheetsService.test_webhook(url)

@app.post("/api/settings/upload-service-account")
async def upload_service_account(file: UploadFile = File(...)):
    try:
        dest = CREDENTIALS_DIR / "service_account.json"
        contents = await file.read()
        with open(dest, "wb") as f:
            f.write(contents)
        
        settings = get_settings()
        settings.sheets_mode = "service_account"
        settings.service_account_file = "credentials/service_account.json"
        save_settings(settings)
        return {"status": "success", "message": "Service account file saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
