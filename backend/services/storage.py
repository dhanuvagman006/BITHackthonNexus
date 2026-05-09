import os
from .verifier import verify_backup

STORAGE_BASE = "storage/backups"
SYSTEMS = ["database", "auth-server", "app-server", "frontend"]

def get_all_backups():
    """Scans all 4 system folders, returns list of all backups with status."""
    results = []
    for system in SYSTEMS:
        system_dir = os.path.join(STORAGE_BASE, system)
        if not os.path.exists(system_dir):
            continue
            
        for f in os.listdir(system_dir):
            if f.endswith(".zip"):
                filepath = os.path.join(system_dir, f)
                status = verify_backup(filepath)
                results.append({
                    "system": system,
                    "filename": f,
                    "filepath": filepath,
                    "status": status,
                    "timestamp": os.path.getmtime(filepath)
                })
    
    results.sort(key=lambda x: x["timestamp"], reverse=True)
    return results

def get_clean_backups():
    """Returns only CLEAN backups."""
    all_backups = get_all_backups()
    return [b for b in all_backups if b["status"] == "CLEAN"]

def get_latest_clean_backup(system: str):
    """Returns latest clean backup dict for a specific system."""
    clean_backups = get_clean_backups()
    system_clean = [b for b in clean_backups if b["system"] == system]
    if not system_clean:
        return None
    return system_clean[0]
