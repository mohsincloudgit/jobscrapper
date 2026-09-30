# 🚀 OmniJob Scraper Pro & Google Sheets Automator

Multi-source live Job Scraper Tool with an interactive Form UI, automatic CSV generation & download, and **automated Date-Wise Google Sheets tab creation & synchronization**.

---

## 🌟 Features / Key Highlights

1. **Expanded Multi-Platform Scraping (8 Integrated Sources):**
   - 💼 **LinkedIn Jobs**: Live verified postings scraped directly from LinkedIn's open guest API.
   - 💬 **Reddit (r/forhire)**: Live direct hiring posts from clients and companies on Reddit social media.
   - 🟠 **HackerNews (YC Startups & Tech Community)**: Real-time "Who is Hiring" posts from founders and engineering leads.
   - 🔴 **RemoteOK**: Global tech, engineering, and remote roles with salary disclosures.
   - 🟠 **WeWorkRemotely (WWR)**: Programming, DevOps, Product, and Support.
   - 🔵 **Jobicy**: Global remote tech & digital roles with geo filters.
   - 🟢 **Arbeitnow**: European and international software engineering & visa-sponsored jobs.
   - 🟣 **Remotive**: Handpicked developer, AI/ML, and marketing roles.
   - *Executed in parallel via async HTTPX for sub-3-second results.*

2. **🎯 "Where to Search" Scope & Categories Selector:**
   - **All Platforms (8 Sources)**: Scrapes across all professional networks, social media, and job boards simultaneously.
   - **💼 Professional Networks**: Focused LinkedIn search.
   - **💬 Social Media & Communities**: Filter specifically for Reddit & HackerNews posts.
   - **🌐 Tech Job Boards**: RemoteOK, WeWorkRemotely, Jobicy, Arbeitnow, Remotive.

3. **⚡ 1-Click Live Deep Search & Social Media Launchers (Dynamic Hub):**
   - Updates in real-time as you type your Job Title & Location:
     - 🔍 **Google Search (Direct ATS Careers)**: Dorks directly for open roles on `site:greenhouse.io OR site:lever.co OR site:jobs.ashbyhq.com`.
     - 🌐 **Google Jobs Dedicated Engine**: Direct pre-filled Google Jobs interface.
     - 💼 **LinkedIn Live Portal**: Filtered for the latest 24-hour job postings.
     - 🐦 **Twitter / X Live Hiring Posts**: Real-time hiring tweets and announcements.
     - 💬 **Reddit Jobs Search**: Live Reddit threads across `r/forhire` and `r/remotejobs`.
     - 🚀 **Wellfound (AngelList)**: Direct startup job search.

3. **CSV Export & In-Browser Download:**
   - Every scrape automatically saves a timestamped CSV in the [`data/`](file:///d:/agide/agide01/data) folder.
   - Generates Excel-compatible UTF-8 BOM CSV files with complete columns:
     `ID`, `Job Title`, `Company`, `Location`, `Date Posted`, `Relative Age`, `Job Type`, `Salary / Compensation`, `Source`, `Job URL`, `Tags`, `Description Snippet`, `Scraped At`.
   - Direct in-browser **"Download CSV"** button.
   - **"Saved CSVs"** drawer to view and download all past scrape files.

4. **Automated Date-Wise Google Sheets Tabs (Daily Tabs):**
   - *"hr new date pe automatically new sheet tab create krke date wise data upload krey"*:
   - Whenever jobs are synced, the tool checks whether a tab for that date exists (e.g. `Jobs_2026-10-01`).
   - If the tab doesn't exist, **it automatically creates a new tab with that date**, styles the header row with dark blue background and cyan text, freezes the header, and appends the jobs.
   - If the tab already exists, it checks existing URLs and **appends only new, non-duplicate jobs**!
   - Supports two flexible connection modes:
     - **Mode 1: Google Apps Script Webhook (Zero GCP Setup, 1-Click Instant)**
     - **Mode 2: Google Cloud Service Account (`service_account.json`)**

---

## 🛠️ Quick Start Guide

### 1. Requirements & Dependencies
Make sure you have Python 3.10+ installed. Dependencies are listed in [`requirements.txt`](file:///d:/agide/agide01/requirements.txt):
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
Run the runner script:
```bash
python run.py
```
Or start via Uvicorn directly:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Open your browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📊 Google Sheets Setup Guide (Date-Wise Tabs)

### Option 1: 1-Click Apps Script Webhook (Fastest & Easiest)
1. Open your [Google Sheets](https://sheets.new) document.
2. In the top menu, click **Extensions** &gt; **Apps Script**.
3. Delete any default code in `Code.gs`.
4. In our web tool, click **"Google Sheet Setup"** &gt; click **"Copy Code"** and paste it into Apps Script.
5. Click **Deploy** &gt; **New deployment**.
   - Select type: **Web app**
   - Description: `Job Scraper Automator`
   - Execute as: **Me**
   - Who has access: **Anyone**
6. Click **Deploy** and copy the **Web App URL** (e.g. `https://script.google.com/macros/s/.../exec`).
7. Paste the Web App URL into the **Webhook URL** field in our tool settings and click **Save Settings**!
8. Now, whenever you scrape or click **"Sync to Google Sheet"**, a new tab with today's date (e.g. `Jobs_2026-10-01`) is created automatically!

### Option 2: Google Cloud Service Account
1. Create a Service Account in the Google Cloud Console with Google Sheets API enabled.
2. Download the JSON key file as [`credentials/service_account.json`](file:///d:/agide/agide01/credentials).
3. Share your Google Sheet with your service account email as **Editor**.
4. In the tool settings, switch to **Method 2: Service Account**, paste your Google Spreadsheet ID, and save!

---

## 📂 Project Architecture

```
agide01/
├── app/
│   ├── main.py                # FastAPI backend & REST endpoints
│   ├── config.py              # Configuration & settings manager
│   ├── scrapers/
│   │   ├── base.py            # JobItem schema & date normalizer
│   │   ├── remoteok.py        # RemoteOK scraper
│   │   ├── weworkremotely.py  # WeWorkRemotely RSS scraper
│   │   ├── jobicy.py          # Jobicy scraper
│   │   ├── arbeitnow.py       # Arbeitnow scraper
│   │   ├── remotive.py        # Remotive scraper
│   │   └── aggregator.py      # Multi-source parallel aggregator & date filter
│   ├── services/
│   │   ├── csv_service.py     # CSV generator & file exporter
│   │   └── sheets_service.py  # Google Sheets auto date-tab creator & sync engine
│   └── static/
│       ├── index.html         # Modern glassmorphism web dashboard
│       ├── css/style.css      # Dark theme styling, animations & responsive grid
│       └── js/app.js          # Interactive frontend controller & search logic
├── data/                      # Auto-saved CSV files and settings.json
├── credentials/               # Folder for optional service_account.json
├── run.py                     # 1-click startup launcher
└── requirements.txt           # Dependency requirements
```

---

## 🇵🇰 Roman Urdu Guide (Mukhtasir Hidayat)

1. **Tool Run krna**:
   - Terminal me `python run.py` likh kr enter karein.
   - Browser me `http://127.0.0.1:8000` open ho jayega.
2. **Form Fill krna**:
   - **Job Title**: Jo job chahiye wo likhein (e.g. `Python`, `React`, `Data Analyst`, waghera).
   - **Location**: `Remote`, `USA`, `Europe` ya `Any` select karein.
   - **Date Filter**: `Today (24h)`, `Past 3 Days`, ya `All Recent` select karein.
   - **Sources**: RemoteOK, WeWorkRemotely, Jobicy, Arbeitnow, Remotive me se jo portals chahiye unhe tick karein.
3. **Scrape & CSV Download**:
   - **"Scrape Latest Jobs"** button dabayein. Chand seconds me fresh jobs load ho jayengi.
   - **"Download CSV"** button dabane se foran Excel-compatible CSV file download ho jayegi.
   - Purani sabhi CSV files dekhne k liye navbar me **"Saved CSVs"** pr click karein.
4. **Google Sheet me Date-Wise Tab Update krna**:
   - Navbar me **"Google Sheet Setup"** open karein.
   - Diya gaya 1-click script copy kr k Google Sheet ke `Extensions -> Apps Script` me paste kr k Deploy as Web App karein.
   - URL paste krke save kr dein.
   - Ab jab bhi jobs sync hongi, **Google Sheet me har nayi date ka alag tab (maslan `Jobs_2026-10-01`) khud-b-khud ban jayega** aur date-wise data add ho jayega!
