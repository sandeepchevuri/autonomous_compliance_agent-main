from agents.extraction_agent import ExtractionAgent
from core.file_utils import save_json_audit
from pathlib import Path
from fastapi import UploadFile
import os

INTERNAL_POLICY_DIR = Path("audit_logs/internal")
INTERNAL_POLICY_DIR.mkdir(parents=True, exist_ok=True)

class CompanyPolicyAgent:
    """
    Wrapper agent for extracting and saving internal company compliance policy data.
    """

    def __init__(self, file: UploadFile):
        self.file = file

    def extract_and_save(self) -> dict:
        """
        Extract structured data from company policy document and save it to internal audit logs.

        Returns:
            dict: Extracted data with metadata.
        """
        extraction_agent = ExtractionAgent(self.file)
        result = extraction_agent.run()

        # Tag this as internal policy data
        result["source"] = "internal_policy"
        result["compliance_type"] = "internal"
        result["filename"] = self.file.filename

        # Save to dedicated internal directory
        json_path = INTERNAL_POLICY_DIR / f"{self.file.filename}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            import json
            json.dump(result, f, indent=2, ensure_ascii=False)

        result["audit_saved_to"] = str(json_path)
        return result
