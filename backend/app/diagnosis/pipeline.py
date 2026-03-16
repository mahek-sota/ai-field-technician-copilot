"""
DiagnosisPipeline — ties together rules engine, prompt builder, LLM client, and response parser.

Flow:
  1. Run rules engine.
     - If high-confidence match found → build DiagnosisResult from RuleMatch, source="rules_fallback"
  2. Build LLM prompt (including rule hints for context).
  3. Call LLM client.
     - On timeout/error → fall back to best rule match if available, else generic fallback.
  4. Parse LLM response.
  5. Return DiagnosisResult with source="llm".
"""
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.diagnosis.prompt_builder import PromptBuilder
from app.diagnosis.response_parser import ResponseParser
from app.diagnosis.rules_engine import RulesEngine, RuleMatch
from app.llm.base import BaseLLMClient
from app.schemas.diagnosis import DiagnosisResult, EvidenceItem, SeverityLevel


def _result_from_rule_match(machine_id: str, match: RuleMatch, source: str = "rules_fallback") -> DiagnosisResult:
    return DiagnosisResult(
        machine_id=machine_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        diagnosis=match.diagnosis,
        recommended_action=match.recommended_action,
        severity=match.severity,
        confidence_score=match.confidence,
        supporting_evidence=match.evidence,
        source=source,
        raw_sensor_snapshot=None,
    )


def _generic_fallback(machine_id: str, error_detail: str) -> DiagnosisResult:
    return DiagnosisResult(
        machine_id=machine_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        diagnosis="Unable to complete automated diagnosis — manual inspection required",
        recommended_action="Dispatch field technician for on-site inspection. Review sensor history in SCADA system.",
        severity=SeverityLevel.MEDIUM,
        confidence_score=0.2,
        supporting_evidence=[
            EvidenceItem(
                description=f"Automated diagnosis failed: {error_detail}",
                source="pattern",
            )
        ],
        source="rules_fallback",
        raw_sensor_snapshot=None,
    )


def _get_llm_client() -> BaseLLMClient:
    if settings.USE_MOCK_LLM:
        from app.llm.mock_client import MockLLMClient
        return MockLLMClient()
    from app.llm.gemini_client import GeminiClient
    return GeminiClient()


async def run_diagnosis_pipeline(machine_id: str, machine_data: dict, use_llm: bool = True) -> DiagnosisResult:
    """
    Standalone wrapper around DiagnosisPipeline.run() for use by external services.
    Set use_llm=False to force rules-only diagnosis (skips LLM call).
    """
    pipeline = DiagnosisPipeline(use_llm=use_llm)
    return await pipeline.run(machine_id=machine_id, raw_data=machine_data)


class DiagnosisPipeline:
    def __init__(self, use_llm: bool = True):
        self._rules = RulesEngine()
        self._prompt_builder = PromptBuilder()
        self._parser = ResponseParser()
        self._use_llm = use_llm

    async def run(self, machine_id: str, raw_data: dict, include_logs: bool = True) -> DiagnosisResult:
        # Step 1 — rules engine
        high_confidence_match = self._rules.evaluate(raw_data)
        if high_confidence_match is not None:
            return _result_from_rule_match(machine_id, high_confidence_match)

        # Collect soft hints for LLM context
        all_matches = self._rules.evaluate_all(raw_data)

        # Step 2 — build prompt
        prompt = self._prompt_builder.build(
            machine_id=machine_id,
            raw_data=raw_data,
            include_logs=include_logs,
            rule_hints=all_matches if all_matches else None,
        )

        # Step 3 — call LLM (skip if use_llm=False)
        if not self._use_llm:
            best_rule = all_matches[0] if all_matches else None
            if best_rule:
                return _result_from_rule_match(machine_id, best_rule)
            return _generic_fallback(machine_id, "LLM disabled and no rules matched")

        llm_client = _get_llm_client()
        sensor_snapshot = {s["name"]: s["value"] for s in raw_data.get("sensors", [])}

        try:
            raw_response = await llm_client.generate(prompt)
        except Exception as exc:
            # LLM failed — fall back to best rule match or generic
            best_rule = all_matches[0] if all_matches else None
            if best_rule is not None:
                return _result_from_rule_match(machine_id, best_rule, source="rules_fallback")
            return _generic_fallback(machine_id, str(exc))

        # Step 4 — parse response
        result = self._parser.parse(
            raw_text=raw_response,
            machine_id=machine_id,
            raw_sensor_snapshot=sensor_snapshot,
        )
        return result
