import os
from pathlib import Path
import pymupdf  # PyMuPDF
from core.analyzer import analyze_text

DOWNLOAD_DIR = Path("downloads")

class AnalyzingAgent:
    def __init__(self):
        self.download_dir = DOWNLOAD_DIR

    def get_latest_pdf(self):
        pdf_files = list(self.download_dir.glob("*.pdf"))
        if not pdf_files:
            return None
        # Find the most recently modified PDF
        latest_file = max(pdf_files, key=lambda x: x.stat().st_mtime)
        return latest_file

    def analyze_latest(self):
        latest_pdf = self.get_latest_pdf()
        if not latest_pdf:
            return {"error": "No PDF found in downloads folder."}

        try:
            text = ""
            with pymupdf.open(latest_pdf) as doc:
                for page in doc:
                    text += page.get_text()
            # Analyze the extracted text
            analysis = analyze_text(text)
            analysis["filename"] = latest_pdf.name
            return analysis
        except Exception as e:
            return {"error": str(e)}
