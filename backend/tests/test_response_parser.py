"""
Tests for ResponseParser — verifies JSON extraction, field coercion, and fallback behavior.
"""
import json
import pytest
from app.diagnosis.response_parser import ResponseParser
from app.schemas.diagnosis import SeverityLevel


@pytest.fixture
def parser():
    return ResponseParser()


def test_parses_clean_json(parser):
    payload = {
        "diagnosis": "Bearing wear detected",
        "recommended_action": "Replace bearing assembly",
        "severity": "high",
        "confidence_score": 0.88,
        "supporting_evidence": [
            {"description": "High vibration reading", "source": "sensor"}
        ],
    }
    result = parser.parse(json.dumps(payload), "machine_1")
    assert result.diagnosis == "Bearing wear detected"
    assert result.severity == SeverityLevel.HIGH
    assert result.confidence_score == 0.88
    assert result.source == "llm"
    assert len(result.supporting_evidence) == 1


def test_parses_json_embedded_in_markdown(parser):
    text = """
Sure! Here is my analysis:

```json
{"diagnosis": "Motor overload", "recommended_action": "Check current draw", "severity": "medium", "confidence_score": 0.75, "supporting_evidence": []}
```
"""
    result = parser.parse(text, "machine_1")
    assert result.diagnosis == "Motor overload"
    assert result.severity == SeverityLevel.MEDIUM


def test_parses_json_embedded_in_prose(parser):
    """JSON buried inside plain text (no code fence) is still extracted."""
    text = 'Based on the data, my assessment is: {"diagnosis": "Seal failure", "recommended_action": "Replace seals", "severity": "high", "confidence_score": 0.82, "supporting_evidence": []} Hope this helps!'
    result = parser.parse(text, "machine_1")
    assert result.diagnosis == "Seal failure"
    assert result.source == "llm"


def test_fallback_on_unparseable_response(parser):
    result = parser.parse("This is not JSON at all, sorry!", "machine_1")
    assert result.source == "rules_fallback"
    assert result.severity == SeverityLevel.MEDIUM
    assert result.confidence_score == pytest.approx(0.3)


def test_fallback_includes_evidence(parser):
    """Even on parse failure the fallback result has at least one evidence item."""
    result = parser.parse("completely unparseable text !!!", "machine_1")
    assert len(result.supporting_evidence) >= 1


def test_missing_fields_get_defaults(parser):
    """Partially-filled JSON: missing fields should get safe defaults."""
    result = parser.parse('{"diagnosis": "Partial response"}', "machine_1")
    assert result.recommended_action  # non-empty default
    assert result.severity == SeverityLevel.MEDIUM
    assert 0.0 <= result.confidence_score <= 1.0


def test_confidence_score_clamped_above_1(parser):
    payload = {
        "diagnosis": "Test",
        "recommended_action": "Test",
        "severity": "low",
        "confidence_score": 1.5,  # invalid — above 1
        "supporting_evidence": [],
    }
    result = parser.parse(json.dumps(payload), "machine_1")
    assert result.confidence_score <= 1.0


def test_confidence_score_clamped_below_0(parser):
    payload = {
        "diagnosis": "Test",
        "recommended_action": "Test",
        "severity": "low",
        "confidence_score": -0.2,  # invalid — below 0
        "supporting_evidence": [],
    }
    result = parser.parse(json.dumps(payload), "machine_1")
    assert result.confidence_score >= 0.0


def test_confidence_exactly_zero(parser):
    payload = {"diagnosis": "T", "recommended_action": "T", "severity": "low",
               "confidence_score": 0.0, "supporting_evidence": []}
    result = parser.parse(json.dumps(payload), "machine_1")
    assert result.confidence_score == pytest.approx(0.0)


def test_confidence_exactly_one(parser):
    payload = {"diagnosis": "T", "recommended_action": "T", "severity": "high",
               "confidence_score": 1.0, "supporting_evidence": []}
    result = parser.parse(json.dumps(payload), "machine_1")
    assert result.confidence_score == pytest.approx(1.0)


def test_unknown_severity_defaults_to_medium(parser):
    payload = {
        "diagnosis": "Test",
        "recommended_action": "Test",
        "severity": "catastrophic",  # not a valid enum value
        "confidence_score": 0.5,
        "supporting_evidence": [],
    }
    result = parser.parse(json.dumps(payload), "machine_1")
    assert result.severity == SeverityLevel.MEDIUM


def test_severity_uppercase_normalized(parser):
    payload = {"diagnosis": "T", "recommended_action": "T",
               "severity": "HIGH", "confidence_score": 0.7, "supporting_evidence": []}
    result = parser.parse(json.dumps(payload), "machine_1")
    assert result.severity == SeverityLevel.HIGH


def test_severity_mixed_case_normalized(parser):
    payload = {"diagnosis": "T", "recommended_action": "T",
               "severity": "Critical", "confidence_score": 0.9, "supporting_evidence": []}
    result = parser.parse(json.dumps(payload), "machine_1")
    assert result.severity == SeverityLevel.CRITICAL


def test_machine_id_preserved_in_result(parser):
    payload = {
        "diagnosis": "Test",
        "recommended_action": "Test",
        "severity": "low",
        "confidence_score": 0.5,
        "supporting_evidence": [],
    }
    result = parser.parse(json.dumps(payload), "pump_4")
    assert result.machine_id == "pump_4"


def test_machine_id_preserved_on_fallback(parser):
    result = parser.parse("not json", "robotic_arm_1")
    assert result.machine_id == "robotic_arm_1"


def test_timestamp_is_populated(parser):
    payload = {"diagnosis": "T", "recommended_action": "T",
               "severity": "low", "confidence_score": 0.5, "supporting_evidence": []}
    result = parser.parse(json.dumps(payload), "machine_1")
    assert result.timestamp  # non-empty


def test_sensor_snapshot_passthrough(parser):
    payload = {"diagnosis": "T", "recommended_action": "T",
               "severity": "low", "confidence_score": 0.5, "supporting_evidence": []}
    snapshot = {"temperature": 85.0, "vibration": 3.2}
    result = parser.parse(json.dumps(payload), "machine_1", raw_sensor_snapshot=snapshot)
    assert result.raw_sensor_snapshot == snapshot


def test_evidence_items_have_description_and_source(parser):
    payload = {
        "diagnosis": "Test",
        "recommended_action": "Test",
        "severity": "high",
        "confidence_score": 0.8,
        "supporting_evidence": [
            {"description": "Vibration above threshold", "source": "sensor"},
            {"description": "Error code E_MOTOR present", "source": "error_code"},
        ],
    }
    result = parser.parse(json.dumps(payload), "machine_1")
    for item in result.supporting_evidence:
        assert item.description
        assert item.source


def test_empty_evidence_list(parser):
    payload = {"diagnosis": "T", "recommended_action": "T",
               "severity": "low", "confidence_score": 0.5, "supporting_evidence": []}
    result = parser.parse(json.dumps(payload), "machine_1")
    assert result.supporting_evidence == []
