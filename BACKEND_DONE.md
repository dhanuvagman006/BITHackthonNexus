# PhoenixVault Backend

## Files Created
- `requirements.txt`: Python dependencies (FastAPI, uvicorn, cryptography).
- `backend/main.py`: FastAPI entry point, handles startup initialization.
- `backend/services/encryption.py`: AES-256 (Fernet) encryption logic and key generation.
- `backend/services/backup_engine.py`: Creates mock encrypted zip files for simulation.
- `backend/services/verifier.py`: Checks backup file hashes and age to determine `CLEAN`, `CORRUPTED`, or `OUTDATED`.
- `backend/services/storage.py`: Scans `storage/backups` directory to locate and verify files.
- `backend/services/index.py`: Maintains `storage/backup_index.json` to store system health status.
- `backend/services/dependency.py`: Defines dependency graph (`auth-server` & `database` -> `app-server` -> `frontend`) and calculates recovery order and estimated time dynamically.
- `backend/services/sandbox.py`: Restores decrypted zips into isolated folders and validates them.
- `backend/services/orchestrator.py`: Runs background recovery process in threads and maintains state (IDLE/RUNNING/COMPLETE) and per-step logs.
- `backend/services/runbook.py`: Generates the automated plain-text incident runbook.
- `backend/routers/backup.py`, `recovery.py`, `dashboard.py`: FastAPI routers mapping to the logic.

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
uvicorn backend.main:app --reload
```

## API Endpoints

### 1. Dashboard Metrics
**Request**: `GET /api/dashboard/metrics`
**Response**:
```json
{
  "readiness_score": 62,
  "total_systems": 4,
  "clean_backups": 5,
  "corrupted_backups": 2,
  "outdated_backups": 1,
  "recovery_status": "IDLE",
  "downtime_seconds": 12,
  "last_backup_time": "2026-05-09 14:40"
}
```

### 2. Recovery Status
**Request**: `GET /api/recovery/status`
**Response**:
```json
{
  "status": "RUNNING",
  "started_at": 1715243123.0,
  "completed_at": null,
  "attack_detected_at": 1715243100.0,
  "systems": {
    "auth-server": "SKIPPED",
    "database": "SKIPPED",
    "app-server": "RESTORING",
    "frontend": "PENDING"
  },
  "log": [
    "[2026-05-09 14:45:23] Recovery order calculated: ['app-server', 'frontend']",
    "[2026-05-09 14:45:23] Skipping auth-server (status is already CLEAN and healthy)",
    "[2026-05-09 14:45:23] Skipping database (status is already CLEAN and healthy)",
    "[2026-05-09 14:45:23] Starting restore for app-server"
  ],
  "total_downtime_seconds": 0
}
```

### 3. Start Recovery
**Request**: `POST /api/recovery/start`
**Response**: `{"message": "Recovery started"}`

### 4. Runbook
**Request**: `GET /api/recovery/runbook`
**Response**: (Plain text Runbook output)

### 5. Dependency Map
**Request**: `GET /api/recovery/dependency-map`
**Response**: JSON dependency graph.

## Full Recovery Flow
1. **Startup**: FastAPI creates mock backups. `database` and `auth-server` have clean latest backups. `app-server` has a corrupted latest backup but a clean older one. `frontend` has only outdated backups.
2. **Dashboard**: `readiness_score` reflects the proportion of clean backups. Downtime counter starts from when the app boots.
3. **Trigger**: User calls `/api/recovery/start`. The orchestrator begins.
4. **Order**: `dependency.py` calculates that only `app-server` and `frontend` need restoring (since auth-server and database are already healthy).
5. **Restore**:
   - `orchestrator` threads grab the latest clean backup for `app-server`.
   - The backup is decrypted and extracted to `sandbox/app-server`.
   - `validate_sandbox` verifies the files are readable.
   - Wait simulation `restore_time_mins * 10` seconds.
   - Proceed sequentially to `frontend` once `app-server` is HEALTHY.
6. **Completion**: Orchestrator sets `status = COMPLETE`, halts the downtime counter, and computes total downtime.

## Frontend Usage
The frontend should routinely poll `/api/dashboard/metrics` and `/api/recovery/status`.
When the user clicks "Start Recovery", POST to `/api/recovery/start` and then show the real-time logs array to visualize progress until `status` becomes `COMPLETE` or `FAILED`.
