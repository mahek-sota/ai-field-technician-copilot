from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


class MachineStatus(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


class SensorReading(BaseModel):
    name: str
    value: float
    unit: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    status: str = "normal"


class MachineInfo(BaseModel):
    machine_id: str
    name: str
    type: str
    location: str
    status: MachineStatus
    last_updated: str
    sensors: List[SensorReading]
    recent_errors: List[str]


class MachineListItem(BaseModel):
    machine_id: str
    name: str
    type: str
    status: MachineStatus
    location: str
