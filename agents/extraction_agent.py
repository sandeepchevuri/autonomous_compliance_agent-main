from core.analyzer import analyze_text
from core.file_utils import extract_text_from_pdf

class ExtractionAgent:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file

    def run(self):
        text = extract_text_from_pdf(self.pdf_file)
        return analyze_text(text)