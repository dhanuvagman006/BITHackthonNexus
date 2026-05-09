SYSTEMS = {
  "auth-server": {"priority": 1, "depends_on": [], "restore_time_mins": 1},
  "database":    {"priority": 2, "depends_on": [], "restore_time_mins": 2},
  "app-server":  {"priority": 3, "depends_on": ["database", "auth-server"], "restore_time_mins": 1},
  "frontend":    {"priority": 4, "depends_on": ["app-server"], "restore_time_mins": 1},
}

def get_restore_order():
    """Returns systems sorted by priority + dependencies resolved.
    Must only return systems whose backup status is CORRUPTED or OUTDATED.
    Skip systems that are already CLEAN and healthy.
    """
    from .index import get_index
    idx = get_index()
    
    needs_restore = []
    for sys, data in idx.items():
        if data["status"] in ["CORRUPTED", "OUTDATED"]:
            needs_restore.append(sys)
            
    # Include dependencies even if they are clean? No, the requirement says:
    # "Don't waste time restoring what isn't broken."
    # So we just restore the broken ones in order.
    # But wait, if app-server is broken, does it require auth-server to be restored FIRST?
    # Yes, but if auth-server is ALREADY healthy, we don't restore it.
    
    order = sorted(needs_restore, key=lambda s: SYSTEMS[s]["priority"])
    return order

def get_dependency_map():
    return SYSTEMS

def estimate_total_recovery_time():
    """Estimate total mins accounting for parallel restores, only for systems needing recovery."""
    order = get_restore_order()
    if not order:
        return 0
        
    # auth-server and database run in parallel. Their max time is 2 mins if both need restore.
    # app-server depends on both.
    # frontend depends on app-server.
    
    time_auth_db = 0
    if "auth-server" in order and "database" in order:
        time_auth_db = max(SYSTEMS["auth-server"]["restore_time_mins"], SYSTEMS["database"]["restore_time_mins"])
    elif "auth-server" in order:
        time_auth_db = SYSTEMS["auth-server"]["restore_time_mins"]
    elif "database" in order:
        time_auth_db = SYSTEMS["database"]["restore_time_mins"]
        
    total = time_auth_db
    
    if "app-server" in order:
        total += SYSTEMS["app-server"]["restore_time_mins"]
        
    if "frontend" in order:
        total += SYSTEMS["frontend"]["restore_time_mins"]
        
    return total
