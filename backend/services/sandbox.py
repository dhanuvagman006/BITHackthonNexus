import os
import shutil

SANDBOX_DIR = "backend/sandbox"

def create_sandbox():
    """Creates clean folder structure under sandbox/."""
    if os.path.exists(SANDBOX_DIR):
        shutil.rmtree(SANDBOX_DIR, ignore_errors=True)
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    for system in ["database", "auth-server", "app-server", "frontend"]:
        os.makedirs(os.path.join(SANDBOX_DIR, system), exist_ok=True)

def restore_to_sandbox(system: str, backup_data: bytes):
    """Writes decrypted backup into sandbox/{system}/"""
    system_dir = os.path.join(SANDBOX_DIR, system)
    os.makedirs(system_dir, exist_ok=True)
    
    import zipfile
    import io
    
    buf = io.BytesIO(backup_data)
    with zipfile.ZipFile(buf, "r") as zf:
        zf.extractall(system_dir)

def validate_sandbox(system: str) -> bool:
    """Checks restored files exist and are readable."""
    system_dir = os.path.join(SANDBOX_DIR, system)
    if not os.path.exists(system_dir):
        return False
        
    files = os.listdir(system_dir)
    if not files:
        return False
        
    for f in files:
        path = os.path.join(system_dir, f)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "rb") as test_f:
                test_f.read(1)
        except Exception:
            return False
            
    return True
