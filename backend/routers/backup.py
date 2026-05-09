from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from ..services.storage import get_all_backups, get_clean_backups, get_latest_clean_backup
from ..services.index import get_index
from ..services.backup_engine import create_backups
from ..services.encryption import decrypt_file

router = APIRouter(prefix="/api/backups", tags=["Backups"])

@router.get("")
def api_get_all_backups():
    return get_all_backups()

@router.get("/clean")
def api_get_clean_backups():
    return get_clean_backups()

@router.get("/index")
def api_get_index():
    return get_index()

@router.get("/restore/{system}")
def api_restore_system(system: str):
    backup = get_latest_clean_backup(system)
    if not backup:
        raise HTTPException(status_code=404, detail="No clean backup found for system")
        
    with open(backup["filepath"], "rb") as f:
        encrypted_data = f.read()
        
    decrypted = decrypt_file(encrypted_data)
    return Response(content=decrypted, media_type="application/zip", headers={
        "Content-Disposition": f"attachment; filename={system}_restored.zip"
    })

@router.post("/create")
def api_create_backups():
    create_backups()
    from ..services.index import update_index
    update_index()
    return {"message": "Backups created and index updated"}
