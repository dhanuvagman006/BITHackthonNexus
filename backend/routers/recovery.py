from fastapi import APIRouter
from ..services.orchestrator import start_recovery, get_recovery_status, reset_recovery
from ..services.dependency import get_restore_order, get_dependency_map, estimate_total_recovery_time
from ..services.runbook import generate_runbook
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/api/recovery", tags=["Recovery"])

@router.post("/start")
def api_start_recovery():
    start_recovery()
    return {"message": "Recovery started"}

@router.get("/status")
def api_get_status():
    return get_recovery_status()

@router.get("/order")
def api_get_order():
    return get_restore_order()

@router.get("/dependency-map")
def api_get_dependency_map():
    return get_dependency_map()

@router.get("/estimate")
def api_get_estimate():
    return {"estimate_mins": estimate_total_recovery_time()}

@router.get("/runbook", response_class=PlainTextResponse)
def api_get_runbook():
    return generate_runbook()

@router.get("/report")
def api_get_report():
    return get_recovery_status()

@router.post("/reset")
def api_reset_recovery():
    reset_recovery()
    return {"message": "Recovery state reset"}
