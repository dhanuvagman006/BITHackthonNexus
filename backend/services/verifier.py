import hashlib
import os
import time

def verify_backup(filepath: str) -> str:
    """Returns 'CLEAN', 'CORRUPTED', or 'OUTDATED'"""
    if not os.path.exists(filepath):
        return "CORRUPTED"
    
    hash_filepath = filepath.replace(".zip", ".hash")
    if not os.path.exists(hash_filepath):
        return "CORRUPTED"
    
    # Calculate SHA256 of the backup file
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    calculated_hash = sha256.hexdigest()
    
    # Read stored hash
    with open(hash_filepath, "r") as f:
        stored_hash = f.read().strip()
        
    if calculated_hash != stored_hash:
        return "CORRUPTED"
        
    # Check if older than 24 hours
    file_stat = os.stat(filepath)
    # Using modification time
    age_seconds = time.time() - file_stat.st_mtime
    if age_seconds > 24 * 3600:
        return "OUTDATED"
        
    return "CLEAN"

def corrupt_backup(filepath: str):
    """Modifies file bytes so hash breaks (simulates attack).
    Also clears read-only bit so we can modify it, then puts it back."""
    if not os.path.exists(filepath):
        return
        
    # Make it writable to corrupt it
    try:
        os.chmod(filepath, 0o644)
    except PermissionError:
        pass # might already be writable or not owned

    with open(filepath, "ab") as f:
        f.write(b"RANSOMWARE_ENCRYPTED_THIS")
    
    # Make it read-only again
    try:
        os.chmod(filepath, 0o444)
    except PermissionError:
        pass
