import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if available
load_dotenv()

AUDIT_DIR = Path("audit_logs")
AUDIT_DIR.mkdir(exist_ok=True)

RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))
CLEANUP_INTERVAL_SECONDS = 3600  # in seconds (1 hour)