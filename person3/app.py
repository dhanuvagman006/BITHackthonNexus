"""
Person 3 — FastAPI Security & Monitoring Backend
=================================================
Central hub for security events, backup status, and alert management.
Provides a REST API for the Terminal Dashboard (dashboard.py) to consume.
"""

import time
import threading
import random
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ──────────────────────────────────────────────
#  Data Models
# ──────────────────────────────────────────────

class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AlertEvent(BaseModel):
    timestamp: str
    severity: Severity
    source: str
    message: str

class SystemStatus(BaseModel):
    name: str
    status: str          # "online" | "compromised" | "recovering" | "restored"
    health_pct: int      # 0-100

class BackupRecord(BaseModel):
    backup_id: str
    created_at: str
    size_mb: float
    integrity: str       # "VERIFIED" | "CORRUPTED" | "PENDING"
    immutable: bool

class RecoveryState(BaseModel):
    active: bool
    phase: str
    progress_pct: int
    elapsed_sec: float
    systems_recovered: int
    systems_total: int

class UserCredentials(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None

class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

# ──────────────────────────────────────────────
#  In-Memory State (shared mutable state)
# ──────────────────────────────────────────────

# --- Security Alerts ---
alert_log: list[dict] = []

# --- Backup Status ---
backup_records: list[dict] = [
    {"backup_id": "BKP-001", "created_at": "2026-05-09T01:00:00Z", "size_mb": 256.4, "integrity": "VERIFIED", "immutable": True},
    {"backup_id": "BKP-002", "created_at": "2026-05-09T04:00:00Z", "size_mb": 128.7, "integrity": "VERIFIED", "immutable": True},
    {"backup_id": "BKP-003", "created_at": "2026-05-09T07:00:00Z", "size_mb": 312.1, "integrity": "VERIFIED", "immutable": True},
    {"backup_id": "BKP-004", "created_at": "2026-05-09T10:00:00Z", "size_mb": 198.3, "integrity": "PENDING", "immutable": True},
]

# --- System Health ---
systems: list[dict] = [
    {"name": "Database (PostgreSQL)", "status": "online", "health_pct": 100},
    {"name": "Authentication Service", "status": "online", "health_pct": 100},
    {"name": "API Gateway", "status": "online", "health_pct": 100},
    {"name": "File Server", "status": "online", "health_pct": 100},
    {"name": "Backup Engine", "status": "online", "health_pct": 100},
]

# --- Recovery ---
recovery_state: dict = {
    "active": False,
    "phase": "IDLE",
    "progress_pct": 0,
    "elapsed_sec": 0.0,
    "systems_recovered": 0,
    "systems_total": len(systems),
    "_start_time": None,
}

# --- Auth ---
USERS_DB = {
    "admin":    {"password": "admin123",    "role": "admin",    "mfa_secret": "123456"},
    "operator": {"password": "operator123", "role": "operator", "mfa_secret": "654321"},
    "viewer":   {"password": "viewer123",   "role": "viewer",   "mfa_secret": "111111"},
}
active_sessions: dict[str, dict] = {}

# --- Attack state ---
attack_active: bool = False
attack_stage: str = "NONE"

# ──────────────────────────────────────────────
#  Helper Functions
# ──────────────────────────────────────────────

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def _add_alert(severity: str, source: str, message: str):
    alert_log.append({
        "timestamp": _now(),
        "severity": severity,
        "source": source,
        "message": message,
    })
    # Keep the log bounded
    if len(alert_log) > 200:
        alert_log.pop(0)

# ──────────────────────────────────────────────
#  FastAPI Application
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Seed initial alerts on startup."""
    _add_alert("INFO", "SYSTEM", "Security backend started successfully")
    _add_alert("INFO", "BACKUP", "All backup channels nominal")
    _add_alert("INFO", "NETWORK", "Perimeter firewall status: ACTIVE")
    yield

app = FastAPI(
    title="PhoenixVault Security Backend",
    description="Person 3 – Security & Monitoring API for the Terminal Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Server is running"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")



# ──────────────────────────────────────────────
#  AUTH Endpoints
# ──────────────────────────────────────────────

@app.post("/auth/login")
def login(creds: UserCredentials):
    user = USERS_DB.get(creds.username)
    if not user or user["password"] != creds.password:
        _add_alert("WARNING", "AUTH", f"Failed login attempt for user '{creds.username}'")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user["role"] == "admin":
        if not creds.totp_code or creds.totp_code != user["mfa_secret"]:
            _add_alert("WARNING", "AUTH", f"MFA challenge failed for admin '{creds.username}'")
            raise HTTPException(status_code=403, detail="MFA required for admin accounts")

    token = f"session-{creds.username}-{int(time.time())}"
    active_sessions[token] = {"username": creds.username, "role": user["role"], "login_time": _now()}
    _add_alert("INFO", "AUTH", f"User '{creds.username}' logged in (role={user['role']})")
    return {"token": token, "role": user["role"]}

@app.get("/auth/sessions")
def list_sessions():
    return {"sessions": active_sessions}

# ──────────────────────────────────────────────
#  STATUS Endpoints
# ──────────────────────────────────────────────

@app.get("/status/systems")
def get_systems():
    return {"systems": systems}

@app.get("/status/backups")
def get_backups():
    return {"backups": backup_records}

@app.get("/status/recovery")
def get_recovery():
    state = dict(recovery_state)
    if state["active"] and state.get("_start_time"):
        state["elapsed_sec"] = round(time.time() - state["_start_time"], 1)
    state.pop("_start_time", None)
    return state

@app.get("/status/overview")
def get_overview():
    """Single endpoint for the dashboard to poll."""
    rec = dict(recovery_state)
    if rec["active"] and rec.get("_start_time"):
        rec["elapsed_sec"] = round(time.time() - rec["_start_time"], 1)
    rec.pop("_start_time", None)
    return {
        "attack_active": attack_active,
        "attack_stage": attack_stage,
        "systems": systems,
        "backups": backup_records,
        "recovery": rec,
        "alerts": alert_log[-30:],   # last 30 alerts
    }

# ──────────────────────────────────────────────
#  ALERTS Endpoints
# ──────────────────────────────────────────────

@app.get("/alerts")
def get_alerts(limit: int = 50):
    return {"alerts": alert_log[-limit:]}

@app.post("/alerts")
def post_alert(alert: AlertEvent):
    _add_alert(alert.severity.value, alert.source, alert.message)
    return {"status": "ok"}

# ──────────────────────────────────────────────
#  ATTACK SIMULATION Endpoints
# ──────────────────────────────────────────────

def _run_attack_sequence():
    """Background thread that simulates a 3-stage ransomware attack."""
    global attack_active, attack_stage

    attack_active = True

    # ── Stage 1: File Encryption ──
    attack_stage = "ENCRYPTION"
    _add_alert("CRITICAL", "RANSOMWARE", "⚠ STAGE 1: File encryption detected on File Server!")
    systems[3]["status"] = "compromised"
    systems[3]["health_pct"] = 30
    time.sleep(3)

    # ── Stage 2: Backup Deletion Attempt ──
    attack_stage = "BACKUP_DELETION"
    _add_alert("CRITICAL", "RANSOMWARE", "⚠ STAGE 2: Attacker attempting to delete backups!")
    _add_alert("INFO", "IMMUTABLE_STORAGE", "✓ Backup deletion BLOCKED — immutable storage protected")
    systems[4]["status"] = "compromised"
    systems[4]["health_pct"] = 70  # partially affected but backups are safe
    time.sleep(3)

    # ── Stage 3: Lateral Movement ──
    attack_stage = "LATERAL_MOVEMENT"
    _add_alert("CRITICAL", "RANSOMWARE", "⚠ STAGE 3: Lateral movement — scanning internal network!")
    systems[0]["status"] = "compromised"
    systems[0]["health_pct"] = 50
    systems[1]["status"] = "compromised"
    systems[1]["health_pct"] = 40
    systems[2]["status"] = "compromised"
    systems[2]["health_pct"] = 60
    time.sleep(2)

    _add_alert("CRITICAL", "RANSOMWARE", "★ ATTACK COMPLETE — All systems compromised!")
    attack_stage = "COMPLETE"


@app.post("/attack/start")
def start_attack():
    global attack_active
    if attack_active:
        raise HTTPException(status_code=409, detail="Attack already in progress")
    _add_alert("CRITICAL", "SIMULATION", "🔴 RANSOMWARE SIMULATION INITIATED")
    thread = threading.Thread(target=_run_attack_sequence, daemon=True)
    thread.start()
    return {"status": "attack_started"}


def _run_recovery_sequence():
    """Background thread that simulates the recovery process."""
    global attack_active, attack_stage
    recovery_state["active"] = True
    recovery_state["phase"] = "INITIALIZING"
    recovery_state["progress_pct"] = 0
    recovery_state["systems_recovered"] = 0
    recovery_state["_start_time"] = time.time()

    _add_alert("INFO", "RECOVERY", "🟢 Recovery orchestrator activated")
    time.sleep(1)

    # Restore each system in dependency order
    restore_order = [
        (0, "Database (PostgreSQL)"),
        (1, "Authentication Service"),
        (2, "API Gateway"),
        (3, "File Server"),
        (4, "Backup Engine"),
    ]

    for i, (idx, name) in enumerate(restore_order):
        recovery_state["phase"] = f"RESTORING: {name}"
        _add_alert("INFO", "RECOVERY", f"Restoring {name} from immutable backup...")
        time.sleep(2)
        systems[idx]["status"] = "restored"
        systems[idx]["health_pct"] = 100
        recovery_state["systems_recovered"] = i + 1
        recovery_state["progress_pct"] = int(((i + 1) / len(restore_order)) * 100)
        _add_alert("INFO", "RECOVERY", f"✓ {name} restored successfully")

    recovery_state["phase"] = "COMPLETE"
    recovery_state["elapsed_sec"] = round(time.time() - recovery_state["_start_time"], 1)
    _add_alert("INFO", "RECOVERY", f"★ FULL RECOVERY COMPLETE in {recovery_state['elapsed_sec']}s")
    attack_active = False
    attack_stage = "NONE"
    recovery_state["active"] = False


@app.post("/attack/recover")
def start_recovery():
    if not attack_active:
        raise HTTPException(status_code=400, detail="No active attack to recover from")
    if recovery_state["active"]:
        raise HTTPException(status_code=409, detail="Recovery already in progress")
    thread = threading.Thread(target=_run_recovery_sequence, daemon=True)
    thread.start()
    return {"status": "recovery_started"}


@app.post("/attack/reset")
def reset_simulation():
    """Reset everything to normal state."""
    global attack_active, attack_stage
    attack_active = False
    attack_stage = "NONE"
    for s in systems:
        s["status"] = "online"
        s["health_pct"] = 100
    recovery_state.update({
        "active": False,
        "phase": "IDLE",
        "progress_pct": 0,
        "elapsed_sec": 0.0,
        "systems_recovered": 0,
        "_start_time": None,
    })
    backup_records[-1]["integrity"] = "PENDING"
    alert_log.clear()
    _add_alert("INFO", "SYSTEM", "Simulation environment reset to clean state")
    return {"status": "reset_complete"}


# ──────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
