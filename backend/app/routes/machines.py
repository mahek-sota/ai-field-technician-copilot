import json
import os
from fastapi import APIRouter, HTTPException
from typing import List
from app.config import settings
from app.schemas.machine import MachineInfo, MachineListItem
from app.schemas.diagnosis import DiagnosisResult
from app.services.machine_service import MachineService

router = APIRouter()
_service = MachineService()


@router.get("/", response_model=List[MachineListItem])
def list_machines():
    """
    Return a summary list of all machines with their current status.

    Response: List[MachineListItem]
      - machine_id: str
      - name: str
      - type: str
      - status: MachineStatus  ("normal" | "warning" | "critical" | "offline")
      - location: str
    """
    return _service.list_machines()


@router.get("/{machine_id}", response_model=MachineInfo)
def get_machine(machine_id: str):
    """
    Return full detail for a single machine including sensor readings and recent error codes.

    Path param: machine_id — matches a subdirectory under data/machines/
    Response: MachineInfo
      - machine_id, name, type, location, status, last_updated
      - sensors: List[SensorReading]
      - recent_errors: List[str]

    Raises 404 if machine_id not found.
    """
    result = _service.get_machine(machine_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found")
    return result


@router.get("/{machine_id}/history", response_model=List[DiagnosisResult])
def get_machine_history(machine_id: str):
    """
    Return the diagnosis history for a machine (most recent first).
    Returns empty list if no history exists. Does not 404 for unknown machines.
    """
    history_path = os.path.join(settings.DATA_DIR, "machines", machine_id, "history.json")
    if not os.path.exists(history_path):
        return []
    try:
        with open(history_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return list(reversed(data))  # most recent first
    except (json.JSONDecodeError, OSError):
        return []
