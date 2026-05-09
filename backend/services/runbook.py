from datetime import datetime
from .index import get_index
from .dependency import get_restore_order, estimate_total_recovery_time

def generate_runbook() -> str:
    idx = get_index()
    order = get_restore_order()
    
    lines = []
    lines.append("PHOENIXVAULT INCIDENT RUNBOOK")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("──────────────────────────────────────────────────")
    lines.append("⚠  RANSOMWARE RECOVERY IN PROGRESS")
    lines.append("")
    lines.append("Step 1: Do NOT pay the ransom")
    lines.append("Step 2: Do NOT restart any affected machines")
    lines.append("Step 3: PhoenixVault has identified the latest clean backups")
    
    step = 4
    systems_to_restore = len(order)
    clean_backups_found = 0
    
    for sys in order:
        clean_backup = idx[sys].get("latest_clean_backup")
        if clean_backup:
            clean_backups_found += 1
            if sys in ["auth-server", "database"]:
                lines.append(f"Step {step}: Restore {sys} from {clean_backup}")
                step += 1
                lines.append(f"Step {step}: Verify {sys} health check passes")
                step += 1
            elif sys == "app-server":
                # Find previous steps for dependencies
                lines.append(f"Step {step}: {sys} will restore automatically after dependencies are met")
                step += 1
            elif sys == "frontend":
                lines.append(f"Step {step}: {sys} will restore automatically after app-server")
                step += 1
                
    total_time = estimate_total_recovery_time()
    
    lines.append("──────────────────────────────────────────────────")
    lines.append(f"SYSTEMS TO RESTORE : {systems_to_restore}")
    lines.append(f"CLEAN BACKUPS FOUND: {clean_backups_found}")
    lines.append(f"ESTIMATED TIME     : {total_time} mins")
    
    return "\n".join(lines)
