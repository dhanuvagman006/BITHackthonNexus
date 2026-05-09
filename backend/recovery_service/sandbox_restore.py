import shutil
import os

BACKUP_SOURCE = "storage/immutable"
RECOVERY_DEST = "storage/recovery"

def restore_latest_backup():

    latest = sorted(os.listdir(BACKUP_SOURCE))[-1]

    source_path = os.path.join(BACKUP_SOURCE, latest)

    shutil.copytree(source_path, RECOVERY_DEST, dirs_exist_ok=True)

    print(f"[+] Backup restored to sandbox")


if __name__ == "__main__":
    restore_latest_backup()