"""
Tests for PromptBuilder — verifies prompt content, structure, and completeness.
"""
import pytest
from app.diagnosis.prompt_builder import PromptBuilder
from app.diagnosis.rules_engine import RulesEngine


@pytest.fixture
def builder():
    return PromptBuilder()


@pytest.fixture
def minimal_raw_data():
    return {
        "info": {"name": "Test Machine", "type": "conveyor", "location": "Floor A"},
        "sensors": [
            {"name": "temperature", "value": 72.0, "unit": "°C",
             "threshold_warning": 80.0, "threshold_critical": 95.0, "status": "normal"},
        ],
        "errors": [],
        "logs": [],
    }


def test_prompt_includes_machine_id(builder, minimal_raw_data):
    assert "conveyor_99" in builder.build("conveyor_99", minimal_raw_data)


def test_prompt_includes_sensor_values(builder, minimal_raw_data):
    prompt = builder.build("test_machine", minimal_raw_data)
    assert "temperature" in prompt.lower()
    assert "72" in prompt


def test_prompt_includes_errors(builder):
    raw = {
        "info": {"name": "X", "type": "conveyor", "location": "A"},
        "sensors": [],
        "errors": ["E_MOTOR_OVERLOAD: Motor current exceeded 150%", "E_TEMP_WARNING: High temp"],
        "logs": [],
    }
    prompt = builder.build("m", raw)
    assert "E_MOTOR_OVERLOAD" in prompt
    assert "E_TEMP_WARNING" in prompt


def test_prompt_includes_json_format_instruction(builder, minimal_raw_data):
    prompt = builder.build("test_machine", minimal_raw_data)
    for field in ("diagnosis", "recommended_action", "severity", "confidence_score", "supporting_evidence"):
        assert field in prompt


def test_prompt_with_no_errors_shows_none(builder):
    raw = {"info": {"name": "X", "type": "conveyor", "location": "A"},
           "sensors": [], "errors": [], "logs": []}
    assert "None" in builder.build("m", raw)


def test_prompt_with_rule_hints(builder, minimal_raw_data):
    engine = RulesEngine()
    hint_data = {
        "sensors": [{"name": "temperature", "value": 85.0, "unit": "°C", "status": "warning"}],
        "errors": [], "logs": [],
    }
    hints = engine.evaluate_all(hint_data)
    assert len(hints) > 0
    prompt = builder.build("test_machine", minimal_raw_data, rule_hints=hints)
    assert "Preliminary Rule-Based Observations" in prompt
    assert any(h.severity.value.upper() in prompt for h in hints)


def test_prompt_length_reasonable(builder, minimal_raw_data):
    prompt = builder.build("test_machine", minimal_raw_data)
    assert len(prompt) < 3000, f"Prompt too long: {len(prompt)} chars"


def test_prompt_excludes_logs_when_flag_false(builder):
    raw = {"info": {"name": "X", "type": "conveyor", "location": "A"},
           "sensors": [], "errors": [],
           "logs": ["UNIQUE_LOG_MARKER_XYZABC\n"]}
    assert "UNIQUE_LOG_MARKER_XYZABC" in builder.build("m", raw, include_logs=True)
    assert "UNIQUE_LOG_MARKER_XYZABC" not in builder.build("m", raw, include_logs=False)


def test_prompt_shows_warning_status_flag(builder):
    raw = {"info": {"name": "X", "type": "conveyor", "location": "A"},
           "sensors": [{"name": "temperature", "value": 85.0, "unit": "°C", "status": "warning"}],
           "errors": [], "logs": []}
    assert "WARNING" in builder.build("m", raw)


def test_prompt_shows_critical_status_flag(builder):
    raw = {"info": {"name": "X", "type": "conveyor", "location": "A"},
           "sensors": [{"name": "temperature", "value": 110.0, "unit": "°C", "status": "critical"}],
           "errors": [], "logs": []}
    assert "CRITICAL" in builder.build("m", raw)


def test_prompt_includes_machine_type(builder, minimal_raw_data):
    assert "conveyor" in builder.build("m", minimal_raw_data).lower()


def test_prompt_no_sensor_data_section(builder):
    raw = {"info": {"name": "X", "type": "conveyor", "location": "A"},
           "sensors": [], "errors": [], "logs": []}
    assert "NO SENSOR DATA AVAILABLE" in builder.build("offline_machine", raw)


def test_prompt_logs_capped_at_20_lines(builder):
    raw = {"info": {"name": "X", "type": "conveyor", "location": "A"},
           "sensors": [], "errors": [],
           "logs": [f"line_{i}\n" for i in range(50)]}
    prompt = builder.build("m", raw, include_logs=True)
    assert "line_49" in prompt
    assert "line_0" not in prompt


def test_prompt_threshold_context_included(builder):
    raw = {"info": {"name": "X", "type": "conveyor", "location": "A"},
           "sensors": [{"name": "temp", "value": 85.0, "unit": "°C",
                         "threshold_warning": 80.0, "threshold_critical": 95.0, "status": "warning"}],
           "errors": [], "logs": []}
    prompt = builder.build("m", raw)
    assert "80.0" in prompt
    assert "95.0" in prompt
