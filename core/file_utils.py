import pymupdf  # PyMuPDF
from pathlib import Path
from datetime import datetime
import json
from core.config import AUDIT_DIR

def extract_text_from_pdf(pdf_file) -> str:
    text = ""
    with pymupdf.open(stream=pdf_file.file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def save_json_audit(data: dict, original_filename: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = original_filename.replace(".pdf", "").replace(" ", "_")
    output_path = AUDIT_DIR / f"{name}_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return str(output_path)