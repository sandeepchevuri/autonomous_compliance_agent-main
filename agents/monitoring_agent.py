import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import os

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

class MonitoringAgent:
    def __init__(self, urls):
        self.urls = urls

    def fetch_and_extract(self):
        updates = []
        for url in self.urls:
            try:
                res = requests.get(url, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")
                for link in soup.find_all("a"):
                    text = link.get_text(strip=True)
                    href = link.get("href")
                    if href and ".pdf" in href.lower() and any(k in text.lower() for k in ["update", "policy", "regulatory"]):
                        full_url = urljoin(url, href)
                        updates.append({"title": text, "url": full_url})
            except Exception as e:
                updates.append({"error": f"Failed to fetch from {url}: {e}"})
        return updates

def monitor_and_download_top_pdf(urls):
    agent = MonitoringAgent(urls)
    updates = agent.fetch_and_extract()

    if updates and "url" in updates[0]:
        pdf_url = updates[0]["url"]
        try:
            response = requests.get(pdf_url)
            filename = os.path.basename(urlparse(pdf_url).path)
            save_path = DOWNLOAD_DIR / filename
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                updates[0]["downloaded_to"] = str(save_path)
            else:
                updates[0]["download_error"] = f"Download failed: {response.status_code}"
        except Exception as e:
            updates[0]["download_error"] = str(e)

    return {"regulatory_updates": updates}
