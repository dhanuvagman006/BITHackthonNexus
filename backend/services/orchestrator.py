import time
import threading
from datetime import datetime
from .index import get_index
from .dependency import get_restore_order, SYSTEMS
from .sandbox import create_sandbox, restore_to_sandbox, validate_sandbox
from .storage import get_clean_backups
from .encryption import decrypt_file
import traceback

global_state = {
    "status": "IDLE",
    "started_at": None,
    "completed_at": None,
    "attack_detected_at": None,
    "systems": {}, 
    "log": [],
    "total_downtime_seconds": 0,
    "external_monitors": {} # {url: {"status": "online", "health_pct": 100, "last_check": None, "components": {}}}
}

def monitor_external_sites():
    """Background loop to check external sites."""
    try:
        import httpx
    except ImportError:
        # Don't crash if httpx is missing, just log it
        print("[!] httpx not found. External monitoring is disabled.")
        return

    # Use a persistent client to reuse connections and avoid port exhaustion timeouts
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        while True:
            urls = list(global_state["external_monitors"].keys())
            for url in urls:
                try:
                    start = time.time()
                    resp = client.get(url)
                    latency = time.time() - start
                    
                    if resp.is_success or resp.is_redirect:
                        global_state["external_monitors"][url]["status"] = "online"
                        # Health based on latency
                        hp = 100 if latency < 0.5 else (80 if latency < 1.5 else 60)
                        global_state["external_monitors"][url]["health_pct"] = hp
                        
                        # Try to extract granular component data if available
                        try:
                            data = resp.json()
                            if isinstance(data, dict) and "systems" in data:
                                # Map external systems to our internal format for the dashboard
                                global_state["external_monitors"][url]["components"] = data["systems"]
                            elif isinstance(data, dict) and "status" in data:
                                # Handle other common health formats
                                global_state["external_monitors"][url]["components"] = data.get("components", {})
                        except:
                            pass # Not a JSON response or doesn't have component data
                            
                        # Try to fetch corruption logs from the external site
                        try:
                            log_url = url.rstrip('/') + '/api/v2/system/corruption-logs'
                            log_resp = client.get(log_url)
                            if log_resp.is_success:
                                ext_logs = log_resp.json()
                                if isinstance(ext_logs, list):
                                    seen = global_state["external_monitors"][url].setdefault("seen_logs", set())
                                    for log_item in ext_logs:
                                        # Format the log item for display
                                        log_str = str(log_item)
                                        if isinstance(log_item, dict):
                                            log_str = log_item.get("message", log_str)
                                            
                                        if log_str not in seen:
                                            seen.add(log_str)
                                            # Add to main event log so it appears in the dashboard
                                            from datetime import datetime
                                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            asset_name = url.replace("https://", "").replace("http://", "").split("/")[0]
                                            global_state["log"].append(f"[{timestamp}] [EXTERNAL: {asset_name}] {log_str}")
                                            
                                        # If there's any corruption log at all, mark the site as compromised
                                        if ext_logs:
                                            global_state["external_monitors"][url]["status"] = "compromised"
                                            global_state["external_monitors"][url]["health_pct"] = 40
                        except Exception as e:
                            print(f"[-] Could not fetch external logs for {url}: {e}")
                    else:
                        global_state["external_monitors"][url]["status"] = "compromised"
                        global_state["external_monitors"][url]["health_pct"] = 40
                        print(f"[!] Monitor alert for {url}: Status {resp.status_code}")
                except Exception as e:
                    global_state["external_monitors"][url]["status"] = "offline"
                    global_state["external_monitors"][url]["health_pct"] = 0
                    print(f"[!] Monitor failed for {url}: {type(e).__name__} - {str(e)}")
                
                global_state["external_monitors"][url]["last_check"] = time.time()
                
            time.sleep(10) # Check every 10 seconds

def log_msg(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    global_state["log"].append(f"[{timestamp}] {msg}")
    print(f"[{timestamp}] {msg}")

def set_attack_time():
    global_state["attack_detected_at"] = time.time()

def _do_restore(system: str):
    log_msg(f"Starting restore for {system}")
    global_state["systems"][system] = "RESTORING"
    
    clean_backups = [b for b in get_clean_backups() if b["system"] == system]
    if not clean_backups:
        log_msg(f"Failed to restore {system}: No clean backups found.")
        global_state["systems"][system] = "FAILED"
        return
        
    for attempt, backup_info in enumerate(clean_backups[:2]):
        try:
            log_msg(f"Attempt {attempt+1}: Decrypting backup {backup_info['filename']} for {system}")
            with open(backup_info["filepath"], "rb") as f:
                encrypted_data = f.read()
            decrypted_data = decrypt_file(encrypted_data)
            
            log_msg(f"Attempt {attempt+1}: Restoring {system} to sandbox")
            restore_to_sandbox(system, decrypted_data)
            
            simulated_time = SYSTEMS[system]["restore_time_mins"] * 10
            log_msg(f"Simulating restore time of {simulated_time}s for {system}...")
            time.sleep(simulated_time)
            
            if validate_sandbox(system):
                log_msg(f"Validation successful for {system}")
                global_state["systems"][system] = "HEALTHY"
                return
            else:
                log_msg(f"Attempt {attempt+1} failed: Validation failed for {system}")
        except Exception as e:
            log_msg(f"Attempt {attempt+1} failed with error for {system}: {str(e)}")
            traceback.print_exc()
            
    log_msg(f"All retry attempts failed for {system}. Marking as FAILED.")
    global_state["systems"][system] = "FAILED"

def _recovery_worker():
    global_state["status"] = "RUNNING"
    global_state["started_at"] = time.time()
    
    create_sandbox()
    
    order = get_restore_order()
    log_msg(f"Recovery order calculated: {order}")
    
    for sys in ["database", "auth-server", "app-server", "frontend"]:
        if sys not in order:
            global_state["systems"][sys] = "SKIPPED"
            log_msg(f"Skipping {sys} (status is already CLEAN and healthy)")
            
    threads = []
    for sys in ["auth-server", "database"]:
        if sys in order:
            t = threading.Thread(target=_do_restore, args=(sys,))
            t.start()
            threads.append((sys, t))
            
    for sys, t in threads:
        t.join()
        
    if "app-server" in order:
        _do_restore("app-server")
        
    if "frontend" in order:
        _do_restore("frontend")
        
    global_state["status"] = "COMPLETE"
    global_state["completed_at"] = time.time()
    
    if global_state["attack_detected_at"]:
        global_state["total_downtime_seconds"] = int(global_state["completed_at"] - global_state["attack_detected_at"])
        
    log_msg(f"Recovery complete. Total downtime: {global_state['total_downtime_seconds']}s")

def start_recovery():
    if global_state["status"] == "RUNNING":
        return
        
    global_state["log"] = []
    for sys in ["database", "auth-server", "app-server", "frontend"]:
        global_state["systems"][sys] = "PENDING"
        
    t = threading.Thread(target=_recovery_worker)
    t.start()

def get_recovery_status():
    return global_state

def reset_recovery():
    global_state["status"] = "IDLE"
    global_state["started_at"] = None
    global_state["completed_at"] = None
    global_state["log"] = []
    global_state["total_downtime_seconds"] = 0
    for sys in ["database", "auth-server", "app-server", "frontend"]:
        global_state["systems"][sys] = "PENDING"
