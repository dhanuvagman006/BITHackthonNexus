import os
import json
from datetime import datetime
from .storage import get_all_backups
from .dependency import SYSTEMS

INDEX_FILE = "storage/backup_index.json"

def update_index():
    """Scans all backups, updates index with latest clean backup per system and status."""
    all_backups = get_all_backups()
    
    index_data = {
        "database": {"latest_clean_backup": None, "status": "PENDING"},
        "auth-server": {"latest_clean_backup": None, "status": "PENDING"},
        "app-server": {"latest_clean_backup": None, "status": "PENDING"},
        "frontend": {"latest_clean_backup": None, "status": "PENDING"}
    }
    
    for system in index_data.keys():
        system_backups = [b for b in all_backups if b["system"] == system]
        
        if not system_backups:
            continue
            
        latest_backup = system_backups[0]
        index_data[system]["status"] = latest_backup["status"]
        
        clean_backups = [b for b in system_backups if b["status"] == "CLEAN"]
        if clean_backups:
            index_data[system]["latest_clean_backup"] = clean_backups[0]["filename"]
            index_data[system]["verified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            index_data[system]["restore_time_estimate_mins"] = SYSTEMS[system]["restore_time_mins"]
        else:
            # If there's no clean backup at all, we keep latest_clean_backup as None
            pass
            
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    with open(INDEX_FILE, "w") as f:
        json.dump(index_data, f, indent=2)

def get_index():
    """Reads and returns index instantly."""
    if not os.path.exists(INDEX_FILE):
        update_index()
    with open(INDEX_FILE, "r") as f:
        return json.load(f)
