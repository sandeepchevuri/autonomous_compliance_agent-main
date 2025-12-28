from difflib import SequenceMatcher
from datetime import datetime
from pathlib import Path
import json

class RiskFlaggerAgent:
    def __init__(self, external_json_path: str, internal_json_path: str):
        self.external_data = self._load_json(external_json_path)
        self.internal_data = self._load_json(internal_json_path)
        self.flags = []

    def _load_json(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _similar(self, a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def _check_mismatches(self, key: str, threshold=0.75):
        external_items = self.external_data.get(key, [])
        internal_items = self.internal_data.get(key, [])
        for ext in external_items:
            if not any(self._similar(ext, int_item) > threshold for int_item in internal_items):
                self.flags.append(f"{key.title()} mismatch or missing: '{ext}' not found in internal policy.")

    def _check_date_mismatches(self):
        external_dates = self.external_data.get("dates", [])
        internal_dates = self.internal_data.get("dates", [])

        try:
            ext_parsed = [datetime.strptime(d, "%Y-%m-%d") for d in external_dates]
            int_parsed = [datetime.strptime(d, "%Y-%m-%d") for d in internal_dates]

            for ed in ext_parsed:
                if not any(abs((ed - id).days) <= 2 for id in int_parsed):  # ±2 days tolerance
                    self.flags.append(f"Date mismatch risk: External deadline {ed.date()} not matched internally.")
        except Exception as e:
            self.flags.append(f"Date parsing issue: {e}")

    def compare(self) -> dict:
        self._check_mismatches("obligations")
        self._check_mismatches("penalties")
        self._check_mismatches("entities")
        self._check_date_mismatches()

        score = max(0, 100 - len(self.flags) * 10)
        return {
            "compliance_score": score,
            "risk_flags": self.flags,
            "external_source": self.external_data.get("filename", "external_unknown"),
            "internal_source": self.internal_data.get("filename", "internal_unknown")
        }
