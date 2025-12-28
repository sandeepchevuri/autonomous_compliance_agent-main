import time
from core.config import AUDIT_DIR, RETENTION_DAYS

def delete_old_audit_logs():
    now = time.time()
    cutoff = now - (RETENTION_DAYS * 86400)
    for file in AUDIT_DIR.glob("*.json"):
        if file.stat().st_mtime < cutoff:
            try:
                file.unlink()
                print(f"[Cleanup] Deleted old file: {file.name}")
            except Exception as e:
                print(f"[Cleanup] Failed to delete {file.name}: {e}")