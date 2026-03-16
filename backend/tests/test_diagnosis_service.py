"""
Tests for DiagnosisService — verifies cache behavior and pipeline delegation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResult, SeverityLevel, EvidenceItem


def _make_result(machine_id="test_machine", source="llm", severity=SeverityLevel.LOW):
    return DiagnosisResult(
        machine_id=machine_id,
        timestamp="2026-03-14T00:00:00+00:00",
        diagnosis="Test diagnosis",
        recommended_action="Test action",
        severity=severity,
        confidence_score=0.9,
        supporting_evidence=[],
        source=source,
    )


@pytest.mark.asyncio
async def test_diagnosis_service_raises_for_unknown_machine():
    from app.services.diagnosis_service import DiagnosisService
    service = DiagnosisService()
    with pytest.raises(ValueError, match="not found"):
        await service.diagnose(DiagnosisRequest(machine_id="definitely_does_not_exist_abc123"))


@pytest.mark.asyncio
async def test_diagnosis_service_uses_cache_on_second_call(sample_raw_data):
    from app.services.diagnosis_service import DiagnosisService

    service = DiagnosisService()

    # Pre-seed the cache using the namespaced key the service actually uses
    cached_result = _make_result(source="cache")
    cached_result.diagnosis = "Cached diagnosis"
    service._cache.set("diagnosis:test_machine", cached_result)

    # Mock machine service so we don't hit disk
    service._machine_service.get_machine_raw_data = MagicMock(return_value=sample_raw_data)

    req = DiagnosisRequest(machine_id="test_machine", force_refresh=False)
    result = await service.diagnose(req)

    assert result.source == "cache"
    assert result.diagnosis == "Cached diagnosis"


@pytest.mark.asyncio
async def test_force_refresh_bypasses_cache(sample_raw_data):
    from app.services.diagnosis_service import DiagnosisService

    service = DiagnosisService()
    service._machine_service.get_machine_raw_data = MagicMock(return_value=sample_raw_data)

    # Pre-seed cache with a stale result
    stale = _make_result(source="cache")
    stale.diagnosis = "Stale"
    service._cache.set("diagnosis:test_machine", stale)

    req = DiagnosisRequest(machine_id="test_machine", force_refresh=True)
    result = await service.diagnose(req)

    # Result should come from pipeline, not cache
    assert result.source != "cache"


@pytest.mark.asyncio
async def test_result_is_stored_in_cache_after_diagnosis(sample_raw_data):
    """After a successful diagnosis, result should be retrievable from cache."""
    from app.services.diagnosis_service import DiagnosisService

    service = DiagnosisService()
    service._machine_service.get_machine_raw_data = MagicMock(return_value=sample_raw_data)

    req = DiagnosisRequest(machine_id="test_machine", force_refresh=True)
    await service.diagnose(req)

    cached = service._cache.get("diagnosis:test_machine")
    assert cached is not None
    assert cached.machine_id == "test_machine"


@pytest.mark.asyncio
async def test_second_call_without_force_refresh_returns_same_result(sample_raw_data):
    """Two consecutive calls return the same cached result on the second call."""
    from app.services.diagnosis_service import DiagnosisService

    service = DiagnosisService()
    service._machine_service.get_machine_raw_data = MagicMock(return_value=sample_raw_data)

    req = DiagnosisRequest(machine_id="test_machine")
    first = await service.diagnose(req)
    second = await service.diagnose(req)

    # Second result is from cache
    assert second.source == "cache"
    assert second.diagnosis == first.diagnosis


@pytest.mark.asyncio
async def test_diagnosis_returns_result_with_machine_id(sample_raw_data):
    from app.services.diagnosis_service import DiagnosisService

    service = DiagnosisService()
    service._machine_service.get_machine_raw_data = MagicMock(return_value=sample_raw_data)

    result = await service.diagnose(DiagnosisRequest(machine_id="test_machine"))
    assert result.machine_id == "test_machine"


@pytest.mark.asyncio
async def test_diagnosis_result_has_valid_source(sample_raw_data):
    from app.services.diagnosis_service import DiagnosisService

    service = DiagnosisService()
    service._machine_service.get_machine_raw_data = MagicMock(return_value=sample_raw_data)

    result = await service.diagnose(DiagnosisRequest(machine_id="test_machine"))
    assert result.source in ("llm", "rules_fallback", "cache")


@pytest.mark.asyncio
async def test_diagnosis_critical_machine_gives_critical_severity(critical_raw_data):
    """Critical-state machine data should produce a critical-severity result via rules."""
    from app.services.diagnosis_service import DiagnosisService

    service = DiagnosisService()
    service._machine_service.get_machine_raw_data = MagicMock(return_value=critical_raw_data)

    result = await service.diagnose(DiagnosisRequest(machine_id="test_machine", force_refresh=True))
    assert result.severity == SeverityLevel.CRITICAL
    assert result.source == "rules_fallback"
