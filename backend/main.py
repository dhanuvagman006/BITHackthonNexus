from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import backup, recovery, dashboard, legacy
from .services.encryption import generate_key
from .services.backup_engine import setup_attack_state
from .services.index import update_index
from .services.orchestrator import set_attack_time, monitor_external_sites
import threading

app = FastAPI(title="PhoenixVault Recovery Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(backup.router)
app.include_router(recovery.router)
app.include_router(dashboard.router)
app.include_router(legacy.router)

@app.on_event("startup")
def startup_event():
    generate_key()
    # No longer seeding mock data or attacks on startup
    update_index()
    # Start external monitoring in background
    threading.Thread(target=monitor_external_sites, daemon=True).start()
