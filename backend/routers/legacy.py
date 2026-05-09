import time
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter

from ..services.orchestrator import global_state, start_recovery, reset_recovery
from ..services.storage import get_all_backups
from ..services.index import get_index, update_index
from ..services.backup_engine import setup_attack_state, setup_clean_state

router = APIRouter(tags=["Legacy Dashboard"])

class UserCredentials(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None

@router.post("/auth/login")
def auth_login(creds: UserCredentials):
    # Dummy login for attack_sim.py
    return {"token": "dummy_token", "role": "admin"}

@router.get("/status/overview")
def status_overview():
    # 1. attack_active
    attack_active = False
    if global_state["attack_detected_at"] and global_state["status"] != "COMPLETE":
        attack_active = True
        
    attack_stage = "COMPLETE" if attack_active else "NONE"
    
    # 2. systems
    sys_list = []
    idx = get_index()
    for sys in ["database", "auth-server", "app-server", "frontend"]:
        # default mapping
        st = "online"
        hp = 100
        
        if attack_active:
            # If the index says it's corrupted and orchestrator is PENDING
            if global_state["systems"][sys] == "PENDING":
                if idx[sys]["status"] in ["CORRUPTED", "OUTDATED"]:
                    st = "compromised"
                    hp = 20
            elif global_state["systems"][sys] == "RESTORING":
                st = "recovering"
                hp = 50
            elif global_state["systems"][sys] == "HEALTHY":
                st = "restored"
                hp = 100
        else:
            if global_state["status"] == "COMPLETE":
                if global_state["systems"][sys] == "HEALTHY":
                    st = "restored"
                    hp = 100
                    
        sys_list.append({
            "name": sys,
            "status": st,
            "health_pct": hp
        })
        
    # 3. backups
    b_list = []
    for b in get_all_backups():
        integrity = "VERIFIED" if b["status"] == "CLEAN" else ("CORRUPTED" if b["status"] == "CORRUPTED" else "PENDING")
        import os
        from datetime import datetime
        created = datetime.fromtimestamp(b["timestamp"]).strftime("%Y-%m-%dT%H:%M:%S")
        size = round(os.path.getsize(b["filepath"]) / (1024 * 1024), 2)
        b_list.append({
            "backup_id": b["filename"],
            "created_at": created,
            "size_mb": size,
            "integrity": integrity,
            "immutable": True
        })
        
    # 4. recovery
    rec_active = global_state["status"] == "RUNNING"
    rec = {
        "active": rec_active,
        "phase": global_state["status"],
        "progress_pct": 0,
        "elapsed_sec": 0,
        "systems_recovered": sum(1 for v in global_state["systems"].values() if v in ["HEALTHY", "SKIPPED"]),
        "systems_total": 4
    }
    
    if global_state["status"] == "RUNNING":
        rec["progress_pct"] = int((rec["systems_recovered"] / 4) * 100)
        rec["elapsed_sec"] = round(time.time() - global_state["started_at"], 1)
    elif global_state["status"] == "COMPLETE":
        rec["progress_pct"] = 100
        rec["elapsed_sec"] = global_state["total_downtime_seconds"]

    # 5. alerts
    alerts = []
    for log_entry in global_state["log"]:
        # logs are like "[2026-05-09 14:45:23] msg"
        parts = log_entry.split("] ", 1)
        ts = parts[0][1:] if len(parts) > 1 else ""
        msg = parts[1] if len(parts) > 1 else log_entry
        alerts.append({
            "severity": "INFO",
            "timestamp": ts,
            "source": "ORCHESTRATOR",
            "message": msg
        })

    return {
        "attack_active": attack_active,
        "attack_stage": attack_stage,
        "systems": sys_list,
        "backups": b_list,
        "recovery": rec,
        "alerts": alerts
    }


@router.post("/attack/start")
def attack_start():
    reset_recovery()
    setup_attack_state()
    update_index()
    from ..services.orchestrator import set_attack_time
    set_attack_time()
    return {"status": "attack_started"}

@router.post("/attack/recover")
def attack_recover():
    start_recovery()
    return {"status": "recovery_started"}

@router.post("/attack/reset")
def attack_reset():
    reset_recovery()
    setup_clean_state()
    update_index()
    # clear attack_detected_at so attack_active becomes False
    global_state["attack_detected_at"] = None
    return {"status": "reset_complete"}
