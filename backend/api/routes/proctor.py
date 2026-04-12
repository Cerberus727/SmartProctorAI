from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import os
import json
from sqlalchemy.orm import Session
from api.services.proctor_service import start_proctor_engine, stop_proctor_engine, generate_frames
from api.schemas.schemas import ResponseModel
from api.dependencies.auth import get_current_user, get_admin_user
from api.models.database import get_db

router = APIRouter()

@router.post("/start", response_model=ResponseModel)
def start_proctor(current_user = Depends(get_current_user)):
    started = start_proctor_engine()
    if started:
        return ResponseModel(success=True, message="started")
    return ResponseModel(success=True, message="already running")

@router.post("/stop", response_model=ResponseModel)
def stop_proctor(current_user = Depends(get_current_user)):
    stop_proctor_engine(force=True)
    return ResponseModel(success=True, message="stopped")

@router.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@router.get("/logs", response_model=ResponseModel)
def get_alerts():
    EVENTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../proctoring_system/events.json"))
    FALLBACK_EVENTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../events.json"))

    target_file = EVENTS_FILE
    if not os.path.exists(target_file):
        if os.path.exists(FALLBACK_EVENTS_FILE):
             target_file = FALLBACK_EVENTS_FILE
        else:
             return ResponseModel(success=True, data=[], message=f"{target_file} not found.")
             
    alerts = []
    try:
        with open(target_file, "r") as f:
            for line in f:
                if line.strip():
                    try: alerts.append(json.loads(line.strip()))
                    except Exception: pass
    except Exception as e:
        return ResponseModel(success=False, message=str(e))
    return ResponseModel(success=True, data=alerts)

from pydantic import BaseModel
class LogViolationRequest(BaseModel):
    test_id: int
    event_type: str

@router.post("/log_violation", response_model=ResponseModel)
def log_violation(data: LogViolationRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    from api.models.domain import ProctorLog
    log_entry = ProctorLog(user_id=current_user.id, test_id=data.test_id, event_type=data.event_type)
    db.add(log_entry)
    db.commit()
    return ResponseModel(success=True, message="Violation logged successfully")
