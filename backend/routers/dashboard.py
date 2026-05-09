import time
from fastapi import APIRouter
from ..services.storage import get_all_backups
from ..services.orchestrator import global_state

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/metrics")
def api_dashboard_metrics():
    all_backups = get_all_backups()
    total = len(all_backups)
    
    clean_count = sum(1 for b in all_backups if b["status"] == "CLEAN")
    corrupted_count = sum(1 for b in all_backups if b["status"] == "CORRUPTED")
    outdated_count = sum(1 for b in all_backups if b["status"] == "OUTDATED")
    
    readiness_score = int((clean_count / total * 100)) if total > 0 else 0
    
    downtime_seconds = 0
    if global_state["status"] == "COMPLETE":
        downtime_seconds = global_state.get("total_downtime_seconds", 0)
    elif global_state["attack_detected_at"]:
        downtime_seconds = int(time.time() - global_state["attack_detected_at"])
        
    last_backup = all_backups[0] if all_backups else None
    from datetime import datetime
    last_backup_time = datetime.fromtimestamp(last_backup["timestamp"]).strftime("%Y-%m-%d %H:%M") if last_backup else None
    
    return {
        "readiness_score": readiness_score,
        "total_systems": 4,
        "clean_backups": clean_count,
        "corrupted_backups": corrupted_count,
        "outdated_backups": outdated_count,
        "recovery_status": global_state["status"],
        "downtime_seconds": downtime_seconds,
        "last_backup_time": last_backup_time
    }
