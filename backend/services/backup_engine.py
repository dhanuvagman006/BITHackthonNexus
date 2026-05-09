import os
import io
import time
import zipfile
import hashlib
from datetime import datetime, timedelta
from .encryption import encrypt_file
from .verifier import corrupt_backup

SYSTEMS = ["database", "auth-server", "app-server", "frontend"]
STORAGE_BASE = "storage/backups"

def _create_mock_zip(system: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{system}_data.txt", f"Mock data for {system}. Timestamp: {datetime.now().isoformat()}")
    return buf.getvalue()

def create_backups():
    """Creates fresh backups for all 4 systems."""
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    for system in SYSTEMS:
        system_dir = os.path.join(STORAGE_BASE, system)
        os.makedirs(system_dir, exist_ok=True)
        
        zip_data = _create_mock_zip(system)
        encrypted_data = encrypt_file(zip_data)
        
        sha256 = hashlib.sha256()
        sha256.update(encrypted_data)
        hash_val = sha256.hexdigest()
        
        backup_path = os.path.join(system_dir, f"backup_{timestamp_str}.zip")
        hash_path = os.path.join(system_dir, f"backup_{timestamp_str}.hash")
        
        if os.path.exists(backup_path):
            os.chmod(backup_path, 0o644)
            
        with open(backup_path, "wb") as f:
            f.write(encrypted_data)
            
        with open(hash_path, "w") as f:
            f.write(hash_val)
            
        os.chmod(backup_path, 0o444)

def setup_attack_state():
    """Creates initial attacked state with a mix of clean, corrupted, and outdated backups."""
    now = datetime.now()
    
    # Clean up existing backups first
    for system in SYSTEMS:
        system_dir = os.path.join(STORAGE_BASE, system)
        if os.path.exists(system_dir):
            for f in os.listdir(system_dir):
                filepath = os.path.join(system_dir, f)
                try:
                    os.chmod(filepath, 0o644)
                except:
                    pass
                os.remove(filepath)

    # 1. database: Latest is CLEAN, also has an older CLEAN
    _create_custom_backup("database", now - timedelta(hours=2), "CLEAN")
    _create_custom_backup("database", now, "CLEAN")
    
    # 2. auth-server: Latest is CLEAN
    _create_custom_backup("auth-server", now, "CLEAN")
    
    # 3. app-server: Latest is CORRUPTED, older is CLEAN
    _create_custom_backup("app-server", now - timedelta(hours=3), "CLEAN")
    _create_custom_backup("app-server", now, "CORRUPTED")
    
    # 4. frontend: Latest is OUTDATED (older than 24h), no fresh backups
    _create_custom_backup("frontend", now - timedelta(days=2), "OUTDATED")
    # And maybe a corrupted one just for fun
    _create_custom_backup("frontend", now - timedelta(days=1), "CORRUPTED")


def setup_clean_state():
    """Resets everything to a clean state with fresh backups for all systems."""
    for system in SYSTEMS:
        system_dir = os.path.join(STORAGE_BASE, system)
        if os.path.exists(system_dir):
            for f in os.listdir(system_dir):
                filepath = os.path.join(system_dir, f)
                try:
                    os.chmod(filepath, 0o644)
                except:
                    pass
                os.remove(filepath)
    create_backups()

def _create_custom_backup(system: str, dt: datetime, status_intent: str):
    timestamp_str = dt.strftime("%Y-%m-%d_%H-%M-%S")
    system_dir = os.path.join(STORAGE_BASE, system)
    os.makedirs(system_dir, exist_ok=True)
    
    zip_data = _create_mock_zip(system)
    encrypted_data = encrypt_file(zip_data)
    
    sha256 = hashlib.sha256()
    sha256.update(encrypted_data)
    hash_val = sha256.hexdigest()
    
    backup_path = os.path.join(system_dir, f"backup_{timestamp_str}.zip")
    hash_path = os.path.join(system_dir, f"backup_{timestamp_str}.hash")
    
    with open(backup_path, "wb") as f:
        f.write(encrypted_data)
        
    with open(hash_path, "w") as f:
        f.write(hash_val)
        
    ts = dt.timestamp()
    os.utime(backup_path, (ts, ts))
    os.utime(hash_path, (ts, ts))
    
    os.chmod(backup_path, 0o444)
    
    if status_intent == "CORRUPTED":
        corrupt_backup(backup_path)
