import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.2)
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass

if __name__ == "__main__":
    print("=" * 65)
    print("🚀 Universal Job Scraper & Google Sheet Automator")
    print("📍 Dashboard URL: http://127.0.0.1:8000")
    print("✨ Multi-source scraping: RemoteOK, WeWorkRemotely, Jobicy, Arbeitnow, Remotive")
    print("📊 Auto Date-wise Google Sheets tab creation & CSV downloads")
    print("=" * 65)
    
    # Optional auto-open browser
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
