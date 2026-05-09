import os
import sys
import time
import subprocess
import threading
import queue
import requests
import hashlib
import shutil
import platform
import io
import concurrent.futures
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
SERVER_FILE = os.path.join(BASE_DIR, "run_server.py")
CORE_DIR = os.path.join(BASE_DIR, "backend")
IMMUTABLE_DIR = os.path.join(BASE_DIR, "backup_server_immutable")
BACKUP_SERVERS = [
    "http://localhost:8001",
    "http://localhost:8002"
]

class ProcessManager:
    def __init__(self):
        self.process = None
        self.restart_count = 0
        self.running = True
        self.log_queue = queue.Queue()
        self.last_hash = self._hash_directory(CORE_DIR)
        
    def _hash_file(self, filepath):
        if not os.path.exists(filepath): return None
        h = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192): h.update(chunk)
            return h.hexdigest()
        except: return None

    def _hash_directory(self, dir_path):
        if not os.path.exists(dir_path): return None
        h = hashlib.sha256()
        for root, dirs, files in os.walk(dir_path):
            parts = root.split(os.sep)
            # Skip noise folders
            if any(x in parts for x in ["__pycache__", "storage", "sandbox", "keys", "snapshots", "templates"]):
                continue
            for name in sorted(files):
                if name.endswith((".pyc", ".pyo")): continue
                filepath = os.path.join(root, name)
                file_hash = self._hash_file(filepath)
                if file_hash: h.update(file_hash.encode())
        return h.hexdigest()

    def log(self, level, message):
        colors = {
            "INFO": Fore.CYAN,
            "SUCCESS": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "SERVER": Fore.WHITE
        }
        color = colors.get(level, Fore.WHITE)
        print(f"{color}[{level}] {message}{Style.RESET_ALL}")

    def start_process(self):
        self.restart_count += 1
        self.log("INFO", f"Starting PhoenixVault Server (restart #{self.restart_count})")
        
        # Port Shield: Ensure port 8000 is clean
        if sys.platform == "win32":
            ps_cmd = "powershell -Command \"$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue; if ($conn) { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue; Start-Sleep -m 500 }\""
            subprocess.run(ps_cmd, shell=True)

        self.process = subprocess.Popen(
            [sys.executable, "-u", SERVER_FILE],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        threading.Thread(target=self._read_logs, args=(self.process,), daemon=True).start()
        self.log("SUCCESS", "System Online and Heartbeat Monitoring Active!")

    def _read_logs(self, process):
        try:
            for line in iter(process.stdout.readline, ''):
                if line: self.log_queue.put(line.strip())
        except: pass

    def stream_logs(self):
        while not self.log_queue.empty():
            line = self.log_queue.get_nowait()
            self.log("SERVER", line)

    def kill_process(self):
        if self.process and self.process.poll() is None:
            self.log("WARNING", f"Killing compromised server process (PID: {self.process.pid})...")
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                self.process.terminate()
            self.process.wait()
            self.process = None

    def check_integrity(self, url):
        try:
            resp = requests.get(f"{url}/check-integrity", timeout=2)
            if resp.status_code == 200 and resp.json().get("status") == "clean":
                return url
        except: pass
        return None

    def recover(self):
        self.log("WARNING", f"Corruption detected! Initializing tiered recovery chain...")
        
        valid_server = None
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(BACKUP_SERVERS)) as executor:
            futures = [executor.submit(self.check_integrity, url) for url in BACKUP_SERVERS]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    valid_server = result
                    break
        
        if valid_server:
            try:
                self.log("INFO", f"Downloading pristine backup from {valid_server}...")
                resp = requests.get(f"{valid_server}/get-backup", timeout=5)
                if resp.status_code == 200:
                    temp_zip = "recovery_temp.zip"
                    with open(temp_zip, "wb") as f: f.write(resp.content)
                    shutil.unpack_archive(temp_zip, ".", "zip")
                    os.remove(temp_zip)
                    self.log("SUCCESS", "System Restored from Remote Backup.")
                    return True
            except Exception as e:
                self.log("ERROR", f"Remote recovery failed: {e}")

        self.log("WARNING", "Remote backups failed. Falling back to local Immutable Snapshot...")
        try:
            imm_zip = os.path.join(IMMUTABLE_DIR, "backend_backup.zip")
            if os.path.exists(imm_zip):
                shutil.unpack_archive(imm_zip, ".")
                self.log("SUCCESS", "Restored successfully from local immutable snapshot!")
                return True
        except Exception as e:
            self.log("ERROR", f"Immutable recovery failed: {e}")
            
        return False

    def monitor(self):
        self.log("INFO", "Self-Healing Supervisor Started.")
        self.start_process()
        
        while self.running:
            time.sleep(1)
            
            # 1. Heartbeat Check
            if self.process and self.process.poll() is not None:
                ret = self.process.poll()
                self.log("ERROR", f"System Failure Detected (Exit Code: {ret})")
                if self.recover():
                    self.last_hash = self._hash_directory(CORE_DIR)
                    self.start_process()
            
            # 2. Integrity Check
            current_hash = self._hash_directory(CORE_DIR)
            if current_hash != self.last_hash:
                self.log("ERROR", "Integrity Breach Detected: Core files tampered with!")
                self.kill_process()
                if self.recover():
                    self.last_hash = self._hash_directory(CORE_DIR)
                    self.start_process()

            self.stream_logs()

if __name__ == "__main__":
    manager = ProcessManager()
    try:
        manager.monitor()
    except KeyboardInterrupt:
        manager.log("INFO", "Shutting down PhoenixVault Manager...")
        manager.kill_process()
