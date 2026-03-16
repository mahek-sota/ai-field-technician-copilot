"""
MachineService — reads machine data from the filesystem data directory.

Data layout expected under DATA_DIR/machines/<machine_id>/:
  - info.json       : static metadata (name, type, location)
  - sensors.json    : current sensor readings array
  - errors.json     : recent error code strings (array)

All methods are synchronous; I/O is local disk reads only.
"""
import json
import os
from datetime import datetime, timezone
from typing import List, Optional

from app.config import settings
from app.schemas.machine import MachineInfo, MachineListItem, MachineStatus, SensorReading


def _machines_root() -> str:
    return os.path.join(settings.DATA_DIR, "machines")


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _derive_status(sensors: List[dict]) -> MachineStatus:
    """Derive overall machine status from sensor readings."""
    has_warning = False
    for s in sensors:
        st = s.get("status", "normal")
        if st == "critical":
            return MachineStatus.CRITICAL
        if st == "warning":
            has_warning = True
    return MachineStatus.WARNING if has_warning else MachineStatus.NORMAL


class MachineService:
    def list_machines(self) -> List[MachineListItem]:
        root = _machines_root()
        if not os.path.isdir(root):
            return []

        items: List[MachineListItem] = []
        for machine_id in sorted(os.listdir(root)):
            machine_dir = os.path.join(root, machine_id)
            if not os.path.isdir(machine_dir):
                continue
            info_path = os.path.join(machine_dir, "info.json")
            sensors_path = os.path.join(machine_dir, "sensors.json")
            if not os.path.exists(info_path):
                continue
            info = _load_json(info_path)
            sensors = _load_json(sensors_path) if os.path.exists(sensors_path) else []
            status = _derive_status(sensors)
            items.append(
                MachineListItem(
                    machine_id=machine_id,
                    name=info.get("name", machine_id),
                    type=info.get("type", "unknown"),
                    status=status,
                    location=info.get("location", "unknown"),
                )
            )
        return items

    def get_machine(self, machine_id: str) -> Optional[MachineInfo]:
        machine_dir = os.path.join(_machines_root(), machine_id)
        if not os.path.isdir(machine_dir):
            return None

        info_path = os.path.join(machine_dir, "info.json")
        sensors_path = os.path.join(machine_dir, "sensors.json")
        errors_path = os.path.join(machine_dir, "errors.json")

        if not os.path.exists(info_path):
            return None

        info = _load_json(info_path)
        raw_sensors = _load_json(sensors_path) if os.path.exists(sensors_path) else []
        recent_errors = _load_json(errors_path) if os.path.exists(errors_path) else []

        sensors = [SensorReading(**s) for s in raw_sensors]
        status = _derive_status(raw_sensors)
        last_updated = datetime.now(timezone.utc).isoformat()

        return MachineInfo(
            machine_id=machine_id,
            name=info.get("name", machine_id),
            type=info.get("type", "unknown"),
            location=info.get("location", "unknown"),
            status=status,
            last_updated=last_updated,
            sensors=sensors,
            recent_errors=recent_errors,
        )

    def get_raw_data(self, machine_id: str) -> Optional[dict]:
        """Return a dict with info, sensors, errors — used by the diagnosis pipeline."""
        machine_dir = os.path.join(_machines_root(), machine_id)
        if not os.path.isdir(machine_dir):
            return None

        info_path = os.path.join(machine_dir, "info.json")
        sensors_path = os.path.join(machine_dir, "sensors.json")
        errors_path = os.path.join(machine_dir, "errors.json")
        # Support both machine.log and logs.txt filenames
        logs_path = os.path.join(machine_dir, "machine.log")
        if not os.path.exists(logs_path):
            logs_path = os.path.join(machine_dir, "logs.txt")

        info = _load_json(info_path) if os.path.exists(info_path) else {}
        sensors = _load_json(sensors_path) if os.path.exists(sensors_path) else []
        errors = _load_json(errors_path) if os.path.exists(errors_path) else []
        logs: List[str] = []
        if os.path.exists(logs_path):
            with open(logs_path, "r", encoding="utf-8") as fh:
                logs = fh.readlines()[-50:]  # last 50 lines

        return {
            "machine_id": machine_id,
            "info": info,
            "sensors": sensors,
            "errors": errors,
            "logs": logs,
        }

    # Alias used by diagnosis_service
    def get_machine_raw_data(self, machine_id: str) -> Optional[dict]:
        return self.get_raw_data(machine_id)
