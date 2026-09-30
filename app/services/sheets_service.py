import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple
import httpx

from app.config import get_settings, BASE_DIR

class GoogleSheetsService:
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
        "Synced At"
    ]

    @staticmethod
    def get_apps_script_code() -> str:
        """Returns the Google Apps Script code that users can paste into Extensions -> Apps Script."""
        return """/**
 * Google Apps Script for Automated Date-Wise Job Sync
 * 1. Open your Google Sheet -> Click Extensions -> Apps Script
 * 2. Delete any existing code, paste this script, and click Save (Ctrl+S)
 * 3. Click Deploy -> New deployment -> Select type: Web app
 * 4. Execute as: 'Me', Who has access: 'Anyone' -> Click Deploy
 * 5. Copy the Web App URL and paste it into the Job Scraper Tool Settings!
 */

function doPost(e) {
  try {
    var rawData = e.postData.contents;
    var data = JSON.parse(rawData);
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    
    var tabName = data.tab_name || ("Jobs_" + Utilities.formatDate(new Date(), "GMT", "yyyy-MM-dd"));
    var headers = data.headers || [
      "ID", "Job Title", "Company", "Location", "Date Posted", 
      "Relative Age", "Job Type", "Salary", "Source", "Job URL", 
      "Tags", "Description Snippet", "Synced At"
    ];
    var jobs = data.jobs || [];
    
    // Check if the date tab exists, if not create it
    var sheet = ss.getSheetByName(tabName);
    var isNewSheet = false;
    
    if (!sheet) {
      sheet = ss.insertSheet(tabName);
      isNewSheet = true;
      sheet.appendRow(headers);
      
      // Style the header row
      var headerRange = sheet.getRange(1, 1, 1, headers.length);
      headerRange.setFontWeight("bold");
      headerRange.setBackground("#0f172a");
      headerRange.setFontColor("#38bdf8");
      headerRange.setHorizontalAlignment("center");
      sheet.setFrozenRows(1);
    }
    
    // Read existing URLs to prevent duplicate uploads
    var existingUrls = {};
    var lastRow = sheet.getLastRow();
    if (lastRow > 1) {
      var urlColValues = sheet.getRange(2, 10, lastRow - 1, 1).getValues();
      for (var i = 0; i < urlColValues.length; i++) {
        var u = urlColValues[i][0];
        if (u) existingUrls[u.toString().trim().toLowerCase()] = true;
      }
    }
    
    var rowsToInsert = [];
    var skippedDuplicates = 0;
    var nowStr = Utilities.formatDate(new Date(), "GMT", "yyyy-MM-dd HH:mm:ss");
    
    for (var j = 0; j < jobs.length; j++) {
      var job = jobs[j];
      var jobUrl = (job.url || "").trim().toLowerCase();
      if (existingUrls[jobUrl]) {
        skippedDuplicates++;
        continue;
      }
      
      var tagsStr = Array.isArray(job.tags) ? job.tags.join(", ") : (job.tags || "");
      
      rowsToInsert.push([
        job.id || "",
        job.title || "",
        job.company || "",
        job.location || "",
        job.date_posted || "",
        job.date_relative || "",
        job.job_type || "",
        job.salary || "",
        job.source || "",
        job.url || "",
        tagsStr,
        job.description_snippet || "",
        nowStr
      ]);
      
      existingUrls[jobUrl] = true;
    }
    
    if (rowsToInsert.length > 0) {
      var startRow = sheet.getLastRow() + 1;
      sheet.getRange(startRow, 1, rowsToInsert.length, headers.length).setValues(rowsToInsert);
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      tab_name: tabName,
      is_new_tab: isNewSheet,
      rows_added: rowsToInsert.length,
      duplicates_skipped: skippedDuplicates,
      total_rows: sheet.getLastRow() - 1,
      spreadsheet_name: ss.getName()
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "online",
    message: "Google Sheet Job Sync Webhook is live and connected!"
  })).setMimeType(ContentService.MimeType.JSON);
}
"""

    @classmethod
    async def sync_via_webhook(
        cls,
        webhook_url: str,
        jobs: List[Dict[str, Any]],
        tab_name: str = ""
    ) -> Dict[str, Any]:
        """Sends job items to the Google Apps Script Webhook."""
        if not webhook_url:
            return {"success": False, "error": "Webhook URL is not configured"}

        if not tab_name:
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            settings = get_settings()
            tab_name = f"{settings.tab_name_prefix}{today_str}"

        payload = {
            "tab_name": tab_name,
            "headers": cls.HEADERS,
            "jobs": jobs
        }

        try:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                resp = await client.post(webhook_url, json=payload)
                if resp.status_code == 200:
                    try:
                        res_json = resp.json()
                        return {
                            "success": True,
                            "mode": "webhook",
                            "tab_name": tab_name,
                            "details": res_json
                        }
                    except Exception:
                        return {
                            "success": True,
                            "mode": "webhook",
                            "tab_name": tab_name,
                            "raw_response": resp.text
                        }
                else:
                    return {
                        "success": False,
                        "error": f"Webhook returned status code {resp.status_code}: {resp.text[:200]}"
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    async def test_webhook(cls, webhook_url: str) -> Dict[str, Any]:
        """Tests connectivity with Google Apps Script Webhook."""
        if not webhook_url:
            return {"success": False, "error": "Webhook URL is empty"}
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(webhook_url)
                if resp.status_code == 200:
                    return {"success": True, "message": "Google Sheet Webhook is active and reachable!"}
                return {"success": False, "error": f"HTTP status {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def sync_via_service_account(
        cls,
        spreadsheet_id: str,
        jobs: List[Dict[str, Any]],
        credentials_file: str = "credentials/service_account.json",
        tab_name: str = ""
    ) -> Dict[str, Any]:
        """Uses official Google Sheets API via gspread and service account."""
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError:
            return {"success": False, "error": "gspread or google-auth not installed"}

        cred_path = BASE_DIR / credentials_file
        if not cred_path.exists():
            return {
                "success": False,
                "error": f"Credentials file '{credentials_file}' not found. Please upload service_account.json"
            }

        if not spreadsheet_id:
            return {"success": False, "error": "Google Spreadsheet ID is empty"}

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        settings = get_settings()
        if not tab_name:
            tab_name = f"{settings.tab_name_prefix}{today_str}"

        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_file(str(cred_path), scopes=scopes)
            client = gspread.authorize(creds)
            
            # Clean ID if full URL was provided
            sheet_id = spreadsheet_id.strip()
            if "/d/" in sheet_id:
                sheet_id = sheet_id.split("/d/")[1].split("/")[0]

            sh = client.open_by_key(sheet_id)

            # Check if tab exists
            worksheets = sh.worksheets()
            ws = None
            is_new_tab = False
            for w in worksheets:
                if w.title == tab_name:
                    ws = w
                    break

            if ws is None:
                # Create new tab with date
                ws = sh.add_worksheet(title=tab_name, rows=max(len(jobs) + 50, 100), cols=len(cls.HEADERS) + 2)
                is_new_tab = True
                ws.append_row(cls.HEADERS)
                # Freeze top row
                try:
                    ws.freeze(rows=1)
                except Exception:
                    pass

            # Read existing URLs to prevent duplicate uploads
            existing_urls = set()
            try:
                url_col = ws.col_values(10)  # 10th column is Job URL
                for u in url_col[1:]:
                    if u:
                        existing_urls.add(u.strip().lower())
            except Exception:
                pass

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            rows_to_insert = []
            skipped = 0

            for j in jobs:
                job_url = (j.get("url") or "").strip().lower()
                if job_url in existing_urls:
                    skipped += 1
                    continue

                tags_str = ", ".join(j.get("tags", [])) if isinstance(j.get("tags"), list) else str(j.get("tags", ""))
                rows_to_insert.append([
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
                    now_str
                ])
                existing_urls.add(job_url)

            if rows_to_insert:
                ws.append_rows(rows_to_insert)

            return {
                "success": True,
                "mode": "service_account",
                "tab_name": tab_name,
                "is_new_tab": is_new_tab,
                "rows_added": len(rows_to_insert),
                "duplicates_skipped": skipped,
                "spreadsheet_title": sh.title,
                "sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    async def sync_jobs(cls, jobs: List[Dict[str, Any]], tab_name: str = "") -> Dict[str, Any]:
        """Automatically dispatches sync according to configured mode."""
        settings = get_settings()
        if settings.sheets_mode == "service_account" and settings.spreadsheet_id:
            # Run in threadpool
            import asyncio
            return await asyncio.to_thread(
                cls.sync_via_service_account,
                spreadsheet_id=settings.spreadsheet_id,
                jobs=jobs,
                credentials_file=settings.service_account_file,
                tab_name=tab_name
            )
        elif settings.apps_script_url:
            return await cls.sync_via_webhook(
                webhook_url=settings.apps_script_url,
                jobs=jobs,
                tab_name=tab_name
            )
        else:
            return {
                "success": False,
                "error": "Google Sheets is not configured yet. Please open Settings and add either a Webhook URL or Service Account."
            }
