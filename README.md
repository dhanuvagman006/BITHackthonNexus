# 🔥 PhoenixVault

**Ransomware-Resilient Backup & Recovery Platform**

> When ransomware hits — PhoenixVault finds the cleanest backup, restores systems in the right order, and tells staff exactly what to do. Minutes not days.

---

## ▶️ Quick Start

```bash
cd phoenixvault
pip install -r requirements.txt
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Open: http://localhost:8000/docs

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/backups` | All backups with CLEAN/CORRUPTED/OUTDATED status |
| GET | `/api/backups/clean` | Only verified clean backups |
| GET | `/api/backups/index` | Pre-built recovery index (zero delay) |
| GET | `/api/backups/restore/{system}` | Decrypt & serve latest clean backup |
| POST | `/api/backups/create` | Create fresh backups for all 4 systems |
| POST | `/api/backups/mark-corrupted/{system}` | Simulate ransomware corruption |

---

## 🗂️ Structure

```
phoenixvault/
├── backend/
│   ├── api/
│   │   ├── main.py                    # FastAPI entry point
│   │   └── routers/
│   │       └── backup.py              # Backup endpoints
│   ├── verifier/
│   │   ├── backup_engine.py           # Creates + compresses + encrypts backups
│   │   ├── encryption.py              # AES-256 encrypt/decrypt
│   │   ├── verifier.py                # SHA256 hash checker
│   │   ├── index.py                   # Recovery-ready backup index
│   │   └── storage.py                 # Immutable storage logic
│   └── keys/
│       └── backup.key                 # Encryption key (auto-generated)
├── storage/backups/
│   ├── database/
│   ├── auth-server/
│   ├── app-server/
│   └── frontend/
├── requirements.txt
└── README.md
```

## 👥 Team

| Person | Role | Folder |
|--------|------|--------|
| Person 1 | Backup & Storage | `backend/verifier/` + `backend/api/routers/backup.py` |
| Person 2 | Recovery & Orchestration | `backend/recovery-engine/` |
| Person 3 | Security & Dashboard | `frontend/` + `backend/simulator/` |
