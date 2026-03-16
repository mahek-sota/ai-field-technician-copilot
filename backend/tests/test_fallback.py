"""
Tests for fallback behavior — verifies the system degrades gracefully when LLM fails.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.schemas.diagnosis import SeverityLevel


@pytest.mark.asyncio
async def test_pipeline_falls_back_to_rules_on_llm_error(sample_raw_data):
    """When LLM raises an exception, pipeline should use best rule match."""
    from app.diagnosis.pipeline import DiagnosisPipeline

    pipeline = DiagnosisPipeline()

    with patch("app.diagnosis.pipeline._get_llm_client") as mock_factory:
        mock_client = MagicMock()
        mock_client.generate = AsyncMock(side_effect=RuntimeError("Gemini API down"))
        mock_factory.return_value = mock_client

        # Use data with a warning-level sensor so a rule match exists
        data_with_warning = dict(sample_raw_data)
        data_with_warning["sensors"] = [
            {"name": "temperature", "value": 85.0, "unit": "°C", "status": "warning"}
        ]
        result = await pipeline.run("test_machine", data_with_warning)

    assert result.source == "rules_fallback"
    assert result.machine_id == "test_machine"


@pytest.mark.asyncio
async def test_pipeline_generic_fallback_when_no_rules_and_llm_fails():
    """When both LLM and rules engine fail, pipeline returns generic fallback."""
    from app.diagnosis.pipeline import DiagnosisPipeline

    pipeline = DiagnosisPipeline()

    with patch("app.diagnosis.pipeline._get_llm_client") as mock_factory:
        mock_client = MagicMock()
        mock_client.generate = AsyncMock(side_effect=RuntimeError("Network error"))
        mock_factory.return_value = mock_client

        # Healthy data — no rules will fire
        healthy_data = {
            "info": {"name": "Test", "type": "conveyor", "location": "A"},
            "sensors": [
                {"name": "temperature", "value": 65.0, "unit": "°C", "status": "normal"},
            ],
            "errors": [],
            "logs": [],
        }
        result = await pipeline.run("test_machine", healthy_data)

    assert result.source == "rules_fallback"
    assert result.severity == SeverityLevel.MEDIUM


@pytest.mark.asyncio
async def test_high_confidence_rule_bypasses_llm(critical_raw_data):
    """If a high-confidence rule fires, the LLM client should never be called."""
    from app.diagnosis.pipeline import DiagnosisPipeline

    pipeline = DiagnosisPipeline()
    llm_called = False

    async def fake_generate(prompt):
        nonlocal llm_called
        llm_called = True
        return "{}"

    with patch("app.diagnosis.pipeline._get_llm_client") as mock_factory:
        mock_client = MagicMock()
        mock_client.generate = AsyncMock(side_effect=fake_generate)
        mock_factory.return_value = mock_client

        result = await pipeline.run("test_machine", critical_raw_data)

    assert not llm_called, "LLM should not be called when high-confidence rule fires"
    assert result.source == "rules_fallback"
    assert result.severity == SeverityLevel.CRITICAL


@pytest.mark.asyncio
async def test_use_llm_false_skips_llm_entirely(sample_raw_data):
    """DiagnosisPipeline(use_llm=False) never calls the LLM factory."""
    from app.diagnosis.pipeline import DiagnosisPipeline

    pipeline = DiagnosisPipeline(use_llm=False)

    with patch("app.diagnosis.pipeline._get_llm_client") as mock_factory:
        data_with_warning = dict(sample_raw_data)
        data_with_warning["sensors"] = [
            {"name": "temperature", "value": 85.0, "unit": "°C", "status": "warning"}
        ]
        result = await pipeline.run("test_machine", data_with_warning)

    mock_factory.assert_not_called()
    assert result.source == "rules_fallback"


@pytest.mark.asyncio
async def test_fallback_result_has_machine_id_and_timestamp():
    """Generic fallback result still has machine_id and non-empty timestamp."""
    from app.diagnosis.pipeline import DiagnosisPipeline

    pipeline = DiagnosisPipeline()

    with patch("app.diagnosis.pipeline._get_llm_client") as mock_factory:
        mock_client = MagicMock()
        mock_client.generate = AsyncMock(side_effect=Exception("timeout"))
        mock_factory.return_value = mock_client

        healthy_data = {
            "info": {"name": "T", "type": "conveyor", "location": "A"},
            "sensors": [{"name": "temperature", "value": 60.0, "unit": "°C", "status": "normal"}],
            "errors": [], "logs": [],
        }
        result = await pipeline.run("my_machine", healthy_data)

    assert result.machine_id == "my_machine"
    assert result.timestamp


@pytest.mark.asyncio
async def test_fallback_result_has_evidence():
    """Generic fallback result includes at least one evidence item."""
    from app.diagnosis.pipeline import DiagnosisPipeline

    pipeline = DiagnosisPipeline()

    with patch("app.diagnosis.pipeline._get_llm_client") as mock_factory:
        mock_client = MagicMock()
        mock_client.generate = AsyncMock(side_effect=Exception("LLM unavailable"))
        mock_factory.return_value = mock_client

        healthy_data = {
            "info": {"name": "T", "type": "conveyor", "location": "A"},
            "sensors": [{"name": "pressure", "value": 4.5, "unit": "bar", "status": "normal"}],
            "errors": [], "logs": [],
        }
        result = await pipeline.run("my_machine", healthy_data)

    assert len(result.supporting_evidence) >= 1
