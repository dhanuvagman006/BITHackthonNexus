import os
import hashlib
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
BACKUP_SERVERS_DIR = os.path.join(BASE_DIR, "backup_servers")
IMMUTABLE_DIR = os.path.join(BASE_DIR, "backup_server_immutable")

def _hash_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192): h.update(chunk)
    return h.hexdigest()

def _hash_directory(dir_path):
    h = hashlib.sha256()
    for root, dirs, files in os.walk(dir_path):
        parts = root.split(os.sep)
        if any(x in parts for x in ["__pycache__", "storage", "sandbox", "keys", "snapshots", "templates"]):
            continue
        for name in sorted(files):
            if name.endswith((".pyc", ".pyo")): continue
            filepath = os.path.join(root, name)
            file_hash = _hash_file(filepath)
            h.update(file_hash.encode())
    return h.hexdigest()

def create_backups():
    print("Creating pristine integrity snapshots...")
    
    # 1. Calculate Hash
    master_hash = _hash_directory(BACKEND_DIR)
    
    # 2. Create ZIP
    zip_path = os.path.join(BASE_DIR, "backend_backup")
    shutil.make_archive(zip_path, 'zip', root_dir='.', base_dir='backend')
    zip_file = zip_path + ".zip"
    
    # 3. Distribute to Backup Servers
    for i in [1, 2]:
        server_dir = os.path.join(BACKUP_SERVERS_DIR, f"server_{i}")
        os.makedirs(server_dir, exist_ok=True)
        
        # Copy ZIP
        shutil.copy(zip_file, os.path.join(server_dir, "backend_backup.zip"))
        
        # Save Hash
        with open(os.path.join(server_dir, "stored_hash.txt"), "w") as f:
            f.write(master_hash)
            
        print(f" -> Backup Server {i} synchronized.")

    # 4. Save to Immutable Local
    os.makedirs(IMMUTABLE_DIR, exist_ok=True)
    shutil.copy(zip_file, os.path.join(IMMUTABLE_DIR, "backend_backup.zip"))
    print(" -> Local Immutable Snapshot secured.")
    
    # Clean up local zip
    os.remove(zip_file)
    print(f"\nSetup Complete! Master Integrity Hash: {master_hash}")

if __name__ == "__main__":
    create_backups()
