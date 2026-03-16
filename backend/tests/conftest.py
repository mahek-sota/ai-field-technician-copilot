"""
pytest configuration and shared fixtures.

Key fixtures:
  - client          : TestClient for the FastAPI app with USE_MOCK_LLM=True
  - sample_raw_data : dict matching MachineService.get_raw_data() output format
  - critical_raw_data : data with critical-temperature sensor for fallback tests
"""
import json
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def use_mock_llm(monkeypatch):
    """Force mock LLM for all tests — no real Gemini calls."""
    monkeypatch.setenv("USE_MOCK_LLM", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    import importlib
    import app.config as cfg
    importlib.reload(cfg)
    cfg.settings.USE_MOCK_LLM = True


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_sensors():
    return [
        {"name": "temperature", "value": 72.3, "unit": "°C",
         "threshold_warning": 80.0, "threshold_critical": 95.0, "status": "normal"},
        {"name": "vibration", "value": 1.2, "unit": "mm/s",
         "threshold_warning": 3.0, "threshold_critical": 6.0, "status": "normal"},
        {"name": "pressure", "value": 4.8, "unit": "bar",
         "threshold_warning": 3.0, "threshold_critical": 2.0, "status": "normal"},
    ]


@pytest.fixture
def critical_sensors():
    return [
        {"name": "temperature", "value": 102.5, "unit": "°C",
         "threshold_warning": 80.0, "threshold_critical": 95.0, "status": "critical"},
        {"name": "vibration", "value": 1.1, "unit": "mm/s",
         "threshold_warning": 3.0, "threshold_critical": 6.0, "status": "normal"},
    ]


@pytest.fixture
def sample_raw_data(sample_sensors):
    return {
        "machine_id": "test_machine",
        "info": {"name": "Conveyor Belt 1", "type": "conveyor", "location": "Factory Floor A"},
        "sensors": sample_sensors,
        "errors": [],
        "logs": ["2026-03-14T10:00:00Z INFO Machine started normally\n"],
    }


@pytest.fixture
def critical_raw_data(critical_sensors):
    return {
        "machine_id": "test_machine",
        "info": {"name": "Conveyor Belt 1", "type": "conveyor", "location": "Factory Floor A"},
        "sensors": critical_sensors,
        "errors": ["E_TEMP_CRITICAL: Temperature exceeded safe operating limit"],
        "logs": [],
    }


@pytest.fixture
def sample_machine_data():
    """Warning-state machine data."""
    return {
        "machine_id": "conveyor_2",
        "info": {"name": "Conveyor Belt 2", "type": "conveyor", "location": "Factory Floor A"},
        "sensors": [
            {"name": "temperature", "value": 78.5, "unit": "°C",
             "threshold_warning": 70.0, "threshold_critical": 85.0, "status": "warning"},
            {"name": "vibration", "value": 2.1, "unit": "mm/s",
             "threshold_warning": 3.0, "threshold_critical": 5.0, "status": "normal"},
        ],
        "errors": ["TEMP_HIGH_001: Temperature exceeded warning threshold"],
        "logs": [
            "2026-03-14T08:05:00Z [WARN] conveyor_2: Temperature rising\n",
            "2026-03-14T08:10:00Z [WARN] conveyor_2: TEMP_HIGH_001 triggered\n",
        ],
    }


@pytest.fixture
def critical_machine_data():
    """Critical-state machine data — joint overheating and high vibration."""
    return {
        "machine_id": "robotic_arm_1",
        "info": {"name": "Robotic Arm 1", "type": "robotic_arm", "location": "Assembly Station C"},
        "sensors": [
            {"name": "joint_temp_1", "value": 102.0, "unit": "°C",
             "threshold_warning": 80.0, "threshold_critical": 95.0, "status": "critical"},
            {"name": "vibration", "value": 4.8, "unit": "mm/s",
             "threshold_warning": 3.0, "threshold_critical": 5.0, "status": "warning"},
        ],
        "errors": [
            "JOINT_OVERHEAT_301: Joint 1 overheating",
            "JOINT_OVERHEAT_301: Joint 1 overheating",
            "JOINT_OVERHEAT_301: Joint 1 overheating",
        ],
        "logs": ["2026-03-14T08:00:00Z [ERROR] robotic_arm_1: JOINT_OVERHEAT_301 critical\n"],
    }


@pytest.fixture
def mock_machine_dir(tmp_path, sample_sensors):
    """Create a temporary machine directory with valid data files."""
    machine_dir = tmp_path / "machines" / "test_machine"
    machine_dir.mkdir(parents=True)
    (machine_dir / "info.json").write_text(json.dumps(
        {"name": "Test Machine", "type": "conveyor", "location": "Test Floor"}
    ))
    (machine_dir / "sensors.json").write_text(json.dumps(sample_sensors))
    (machine_dir / "errors.json").write_text(json.dumps([]))
    return tmp_path
