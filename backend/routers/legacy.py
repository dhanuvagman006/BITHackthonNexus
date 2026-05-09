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

    # 6. External Monitors
    ext_list = []
    for url, data in global_state["external_monitors"].items():
        ext_list.append({
            "name": url.replace("https://", "").replace("http://", "").split("/")[0],
            "url": url,
            "status": data["status"],
            "health_pct": data["health_pct"],
            "components": data.get("components", []), # Include sub-components
            "backup_hash": data.get("backup_hash", "N/A"),
            "backup_records": data.get("backup_records", 0),
            "backup_size_kb": data.get("backup_size_kb", 0)
        })

    return {
        "attack_active": attack_active,
        "attack_stage": attack_stage,
        "systems": sys_list,
        "backups": b_list,
        "recovery": rec,
        "alerts": alerts,
        "external_sites": ext_list
    }


@router.post("/monitor/add")
def monitor_add(url: str):
    if url not in global_state["external_monitors"]:
        global_state["external_monitors"][url] = {
            "status": "pending", 
            "health_pct": 100, 
            "last_check": None, 
            "components": {}, 
            "seen_logs": set(),
            "backup_data": None
        }
        
        # Automate backup upon connection
        import httpx
        try:
            target = url.rstrip("/") + "/api/v2/system/export-data"
            resp = httpx.get(target, timeout=5)
            if resp.status_code == 200:
                res_data = resp.json()
                if res_data.get("status") == "success":
                    import json
                    import hashlib
                    import os
                    from datetime import datetime
                    
                    # Store as a physical snapshot file on disk
                    os.makedirs("snapshots", exist_ok=True)
                    host_clean = url.replace("https://", "").replace("http://", "").split("/")[0].replace(":", "_")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    snapshot_file = f"snapshots/snapshot_{host_clean}_{timestamp}.json"
                    
                    data_bytes = json.dumps(res_data.get("data")).encode('utf-8')
                    with open(snapshot_file, 'wb') as f:
                        f.write(data_bytes)
                        
                    global_state["external_monitors"][url]["snapshot_file"] = snapshot_file
                    global_state["external_monitors"][url]["backup_hash"] = hashlib.sha256(data_bytes).hexdigest()[:12]
                    global_state["external_monitors"][url]["backup_records"] = len(res_data.get("data", []))
                    global_state["external_monitors"][url]["backup_size_kb"] = len(data_bytes) // 1024
                    
                    # Add normal log
                    ts_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    global_state["log"].append(f"[{ts_log}] [EXTERNAL] Snapshot secured to {snapshot_file} ({global_state['external_monitors'][url]['backup_size_kb']} KB).")
        except:
            pass # Fail silently if endpoint doesn't exist


            
        return {"status": "added", "url": url}
    return {"status": "exists"}

@router.post("/monitor/fix")
def monitor_fix(url: str):
    """Attempt to trigger a recovery on the external site."""
    if url in global_state["external_monitors"]:
        import httpx
        try:
            snapshot_file = global_state["external_monitors"][url].get("snapshot_file")
            import json
            import os
            backup_data = None
            if snapshot_file and os.path.exists(snapshot_file):
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
            
            # First try the specific data correction endpoint we added for the external monitor
            target = url.rstrip("/") + "/api/v2/system/restore-data"
            payload = {"data": backup_data} if backup_data else {}

            
            resp = httpx.post(target, json=payload, timeout=10)
            if resp.status_code == 200:
                # Clear the seen corruption logs locally so the site recovers in our dashboard
                global_state["external_monitors"][url]["seen_logs"] = set()
                global_state["external_monitors"][url]["status"] = "online"
                global_state["external_monitors"][url]["health_pct"] = 100
                
                from datetime import datetime
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                global_state["log"].append(f"[{ts}] [EXTERNAL] Data restored on {url}. Breach cleared.")
                
                return {"status": "repair_initiated", "target": target}
            
            # Fallback to the old recovery endpoint
            target = url.rstrip("/") + "/attack/recover"
            resp = httpx.post(target, timeout=5)
            if resp.status_code == 200:
                return {"status": "repair_initiated", "target": target}
            else:
                return {"status": "repair_failed", "code": resp.status_code}
        except Exception as e:
            return {"status": "repair_error", "error": str(e)}
    return {"status": "not_found"}


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
