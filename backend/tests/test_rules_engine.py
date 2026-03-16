"""
Tests for RulesEngine — verifies each rule fires correctly with known inputs.
"""
import pytest
from app.diagnosis.rules_engine import RulesEngine, HIGH_CONFIDENCE_THRESHOLD
from app.schemas.diagnosis import SeverityLevel


@pytest.fixture
def engine():
    return RulesEngine()


def test_high_temperature_detected(engine):
    raw_data = {
        "sensors": [{"name": "temperature", "value": 110.0, "unit": "°C",
                      "threshold_warning": 80.0, "threshold_critical": 95.0, "status": "critical"}],
        "errors": [], "logs": [],
    }
    match = engine.evaluate(raw_data)
    assert match is not None
    assert match.severity == SeverityLevel.CRITICAL
    assert match.confidence >= HIGH_CONFIDENCE_THRESHOLD
    assert "temperature" in match.diagnosis.lower()


def test_normal_sensors_no_rules_match(engine):
    raw_data = {
        "sensors": [
            {"name": "temperature", "value": 65.0, "unit": "°C", "status": "normal"},
            {"name": "vibration", "value": 1.0, "unit": "mm/s", "status": "normal"},
            {"name": "pressure", "value": 5.0, "unit": "bar", "status": "normal"},
        ],
        "errors": [], "logs": [],
    }
    assert engine.evaluate(raw_data) is None


def test_high_vibration_detected(engine):
    raw_data = {
        "sensors": [{"name": "vibration_x", "value": 8.5, "unit": "mm/s",
                      "threshold_warning": 3.0, "threshold_critical": 6.0, "status": "critical"}],
        "errors": [], "logs": [],
    }
    match = engine.evaluate(raw_data)
    assert match is not None
    assert match.severity == SeverityLevel.CRITICAL
    assert match.confidence >= HIGH_CONFIDENCE_THRESHOLD


def test_combined_temp_vibration_produces_match(engine):
    """Both temp (warning) and vibration (warning) together triggers combined rule."""
    raw_data = {
        "sensors": [
            {"name": "temperature", "value": 85.0, "unit": "°C",
             "threshold_warning": 80.0, "threshold_critical": 95.0, "status": "warning"},
            {"name": "vibration", "value": 4.0, "unit": "mm/s",
             "threshold_warning": 3.0, "threshold_critical": 6.0, "status": "warning"},
        ],
        "errors": [], "logs": [],
    }
    matches = engine.evaluate_all(raw_data)
    assert len(matches) >= 1
    # Combined rule should appear
    combined = next((m for m in matches if "bearing" in m.diagnosis.lower()), None)
    assert combined is not None
    assert combined.severity == SeverityLevel.HIGH


def test_low_pressure_detected(engine):
    raw_data = {
        "sensors": [{"name": "outlet_pressure", "value": 1.8, "unit": "bar",
                      "threshold_warning": 3.0, "threshold_critical": 2.0, "status": "critical"}],
        "errors": [], "logs": [],
    }
    match = engine.evaluate(raw_data)
    assert match is not None
    assert match.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)
    assert match.confidence >= HIGH_CONFIDENCE_THRESHOLD


def test_recurring_errors_rule(engine):
    """Motor overload error code triggers motor overload rule."""
    raw_data = {
        "sensors": [{"name": "temperature", "value": 65.0, "unit": "°C", "status": "normal"}],
        "errors": [
            "E_MOTOR_OVERLOAD: Motor current exceeded 150%",
            "E_MOTOR_OVERLOAD: Motor current exceeded 150%",
            "E_MOTOR_OVERLOAD: Motor current exceeded 150%",
        ],
        "logs": [],
    }
    match = engine.evaluate(raw_data)
    assert match is not None
    assert match.severity == SeverityLevel.HIGH
    assert "motor" in match.diagnosis.lower()


def test_rules_sorted_by_confidence(engine):
    """Critical temp rule (0.95) has higher confidence than motor overload rule (0.90)."""
    raw_data = {
        "sensors": [{"name": "temperature", "value": 110.0, "unit": "°C", "status": "critical"}],
        "errors": ["E_MOTOR_OVERLOAD"],
        "logs": [],
    }
    matches = engine.evaluate_all(raw_data)
    assert len(matches) >= 2
    temp_match = next((m for m in matches if "temperature" in m.diagnosis.lower()), None)
    motor_match = next((m for m in matches if "motor" in m.diagnosis.lower()), None)
    if temp_match and motor_match:
        assert temp_match.confidence > motor_match.confidence


def test_rule_match_has_evidence(engine):
    raw_data = {
        "sensors": [{"name": "temperature", "value": 102.0, "unit": "°C", "status": "critical"}],
        "errors": [], "logs": [],
    }
    for match in engine.evaluate_all(raw_data):
        assert len(match.evidence) > 0


def test_rule_match_has_severity(engine):
    raw_data = {
        "sensors": [{"name": "temperature", "value": 102.0, "unit": "°C", "status": "critical"}],
        "errors": ["E_MOTOR_OVERLOAD"],
        "logs": [],
    }
    for match in engine.evaluate_all(raw_data):
        assert match.severity in set(SeverityLevel)


def test_critical_machine_data_returns_critical_severity(engine, critical_machine_data):
    raw_data = {
        "sensors": critical_machine_data["sensors"],
        "errors": critical_machine_data["errors"],
        "logs": critical_machine_data["logs"],
    }
    match = engine.evaluate(raw_data)
    assert match is not None
    assert match.severity == SeverityLevel.CRITICAL


def test_no_sensors_triggers_offline_rule(engine):
    raw_data = {"sensors": [], "errors": [], "logs": []}
    match = engine.evaluate(raw_data)
    assert match is not None
    assert match.confidence >= HIGH_CONFIDENCE_THRESHOLD
    assert match.severity == SeverityLevel.HIGH


def test_evaluate_all_returns_multiple_matches(engine):
    raw_data = {
        "sensors": [{"name": "temperature", "value": 85.0, "unit": "°C", "status": "warning"}],
        "errors": ["E_MOTOR_OVERLOAD"],
        "logs": [],
    }
    assert len(engine.evaluate_all(raw_data)) >= 2


def test_warning_temperature_below_high_confidence_threshold(engine):
    """Warning-temp rule (confidence=0.80) must NOT short-circuit the pipeline."""
    raw_data = {
        "sensors": [{"name": "temperature", "value": 85.0, "unit": "°C", "status": "warning"}],
        "errors": [], "logs": [],
    }
    assert engine.evaluate(raw_data) is None
    matches = engine.evaluate_all(raw_data)
    temp_warning = next((m for m in matches if m.severity == SeverityLevel.MEDIUM), None)
    assert temp_warning is not None


def test_pressure_with_error_code_adds_evidence(engine):
    raw_data = {
        "sensors": [{"name": "outlet_pressure", "value": 1.5, "unit": "bar", "status": "critical"}],
        "errors": ["E_PRESSURE_LOW: Outlet pressure below minimum"],
        "logs": [],
    }
    matches = engine.evaluate_all(raw_data)
    pressure_match = next((m for m in matches if "pressure" in m.diagnosis.lower()), None)
    assert pressure_match is not None
    assert len(pressure_match.evidence) >= 2
