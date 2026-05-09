# Recommended Project Structure

```text id="z4r8r4"
ransomware-recovery-system/
│
├── backend/
│   ├── backup_service/
│   ├── recovery_service/
│   ├── security_monitor/
│   ├── shared/
│   └── main.py
│
├── frontend/
│   ├── src/
│   └── package.json
│
├── storage/
│   ├── primary/
│   ├── immutable/
│   └── recovery/
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

This structure allows all 3 people to work independently.

---

# Person 1 — Backup & Immutable Storage

## Folder

```text id="8kgqwh"
backend/backup_service/
```

---

# Starter Code — backup_manager.py

```python
# backend/backup_service/backup_manager.py

import os
import shutil
import hashlib
from datetime import datetime

SOURCE_DIR = "storage/primary"
BACKUP_DIR = "storage/immutable"

def calculate_hash(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            sha256.update(chunk)

    return sha256.hexdigest()


def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, timestamp)

    os.makedirs(backup_path, exist_ok=True)

    for file in os.listdir(SOURCE_DIR):
        src = os.path.join(SOURCE_DIR, file)
        dst = os.path.join(backup_path, file)

        shutil.copy2(src, dst)

        file_hash = calculate_hash(dst)

        with open(dst + ".hash", "w") as h:
            h.write(file_hash)

    print(f"[+] Backup created: {backup_path}")


if __name__ == "__main__":
    create_backup()
```

---

# Starter Code — verifier.py

```python
# backend/backup_service/verifier.py

import hashlib
import os

BACKUP_DIR = "storage/immutable"

def calculate_hash(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            sha256.update(chunk)

    return sha256.hexdigest()


def verify_backup(folder):
    for file in os.listdir(folder):

        if file.endswith(".hash"):
            continue

        file_path = os.path.join(folder, file)
        hash_path = file_path + ".hash"

        with open(hash_path, "r") as h:
            stored_hash = h.read()

        current_hash = calculate_hash(file_path)

        if stored_hash != current_hash:
            print(f"[!] Corruption detected: {file}")
        else:
            print(f"[OK] {file} verified")


if __name__ == "__main__":
    latest = sorted(os.listdir(BACKUP_DIR))[-1]
    verify_backup(os.path.join(BACKUP_DIR, latest))
```

---

# Person 2 — Recovery Orchestration

## Folder

```text id="2osjlwm"
backend/recovery_service/
```

---

# Starter Code — dependency_map.py

```python
# backend/recovery_service/dependency_map.py

DEPENDENCIES = {
    "database": [],
    "auth_service": ["database"],
    "backend_api": ["auth_service"],
    "frontend": ["backend_api"]
}
```

---

# Starter Code — recovery_engine.py

```python
# backend/recovery_service/recovery_engine.py

import time
from dependency_map import DEPENDENCIES

restored = set()

def restore_service(service):

    if service in restored:
        return

    dependencies = DEPENDENCIES[service]

    for dep in dependencies:
        restore_service(dep)

    print(f"[+] Restoring {service}...")
    time.sleep(2)

    print(f"[OK] {service} restored")

    restored.add(service)


def start_recovery():
    for service in DEPENDENCIES:
        restore_service(service)


if __name__ == "__main__":
    start_recovery()
```

---

# Starter Code — sandbox_restore.py

```python
# backend/recovery_service/sandbox_restore.py

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
```

---

# Person 3 — Security & Dashboard

## Folder

```text id="ujm8g4"
backend/security_monitor/
frontend/
```

---

# Starter Code — ransomware_simulator.py

```python
# backend/security_monitor/ransomware_simulator.py

import os

TARGET_DIR = "storage/primary"

def simulate_attack():

    for file in os.listdir(TARGET_DIR):

        path = os.path.join(TARGET_DIR, file)

        if os.path.isfile(path):

            with open(path, "w") as f:
                f.write("ENCRYPTED_BY_RANSOMWARE")

    print("[!] Ransomware attack simulated")


if __name__ == "__main__":
    simulate_attack()
```

---

# Starter Code — monitor.py

```python
# backend/security_monitor/monitor.py

import os
import time

WATCH_DIR = "storage/primary"

def monitor():

    while True:

        suspicious = False

        for file in os.listdir(WATCH_DIR):

            path = os.path.join(WATCH_DIR, file)

            with open(path, "r", errors="ignore") as f:

                content = f.read()

                if "ENCRYPTED_BY_RANSOMWARE" in content:
                    suspicious = True

        if suspicious:
            print("[ALERT] Possible ransomware detected!")

        time.sleep(5)


if __name__ == "__main__":
    monitor()
```

---

# Frontend Starter (React)

## File

```text id="ry0tdo"
frontend/src/App.js
```

---

# Starter Dashboard

```javascript
import React from "react";

function App() {
  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>Ransomware Recovery Dashboard</h1>

      <div>
        <h2>System Status</h2>
        <p>Backup Status: Healthy</p>
        <p>Recovery Readiness: Ready</p>
        <p>Threat Detection: No Active Threats</p>
      </div>

      <div>
        <h2>Recovery Timeline</h2>
        <ul>
          <li>09:00 - Backup Created</li>
          <li>09:10 - Threat Detected</li>
          <li>09:12 - Recovery Started</li>
          <li>09:15 - Systems Restored</li>
        </ul>
      </div>
    </div>
  );
}

export default App;
```

---

# Main FastAPI Entry Point

## File

```text id="5vw4c7"
backend/main.py
```

---

# Starter API

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "Ransomware Recovery System Running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
```

---

# Docker Compose Starter

## File

```text id="7g3u7u"
docker-compose.yml
```

---

```yaml
version: '3'

services:

  backend:
    build: .
    ports:
      - "8000:8000"

    volumes:
      - ./storage:/app/storage

    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000

  frontend:
    image: node:18
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "3000:3000"
    command: sh -c "npm install && npm start"
```

---

# requirements.txt

```txt
fastapi
uvicorn
python-multipart
```

---

# Suggested Workflow

## Day 1

| Person | Task                         |
| ------ | ---------------------------- |
| P1     | Backup engine + verification |
| P2     | Recovery orchestrator        |
| P3     | Dashboard + attack simulator |

---

## Day 2

Integrate:

* attack → detection → restore → dashboard updates

---

# Best Demo Flow

```text id="eq4ezu"
1. Upload files to primary storage
2. Run automated backup
3. Trigger ransomware simulator
4. Dashboard shows attack alert
5. Recovery engine starts
6. Sandbox restore completes
7. Services come back online
```

---

# High-Impact Features (If Time Allows)

## Add these later

### P1

* Encryption
* Deduplication
* S3/MinIO integration

### P2

* Parallel restore
* Dependency visualization
* Health checks

### P3

* Live charts
* WebSocket alerts
* Recovery metrics

---

# Important Hackathon Advice

Your judges will care more about:

* clear architecture,
* realistic ransomware workflow,
* and smooth demo execution

than about huge amounts of code.

Focus on:

* attack simulation,
* immutable backup,
* automated recovery,
* and clean visualization.
