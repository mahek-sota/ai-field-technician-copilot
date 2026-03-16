"""
ResponseParser — extracts a DiagnosisResult from the raw LLM text response.

Strategy:
  1. Try to parse the entire response as JSON.
  2. If that fails, extract the first {...} block using a regex and parse that.
  3. If that also fails, return a fallback DiagnosisResult with source="rules_fallback".

The parser is lenient: it coerces severity strings to SeverityLevel and clips
confidence_score to [0.0, 1.0].
"""
import json
import re
from datetime import datetime, timezone
from typing import Optional

from app.schemas.diagnosis import DiagnosisResult, EvidenceItem, SeverityLevel


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _coerce_severity(raw: str) -> SeverityLevel:
    mapping = {
        "low": SeverityLevel.LOW,
        "medium": SeverityLevel.MEDIUM,
        "high": SeverityLevel.HIGH,
        "critical": SeverityLevel.CRITICAL,
    }
    return mapping.get(str(raw).strip().lower(), SeverityLevel.MEDIUM)


def _parse_json_block(text: str) -> Optional[dict]:
    """Try to extract and parse the first JSON object from text."""
    # Attempt 1 — entire text
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Attempt 2 — first {...} block (handles markdown code fences etc.)
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


class ResponseParser:
    def parse(
        self,
        raw_text: str,
        machine_id: str,
        raw_sensor_snapshot: Optional[dict] = None,
    ) -> DiagnosisResult:
        timestamp = datetime.now(timezone.utc).isoformat()
        parsed = _parse_json_block(raw_text)

        if parsed is None:
            return DiagnosisResult(
                machine_id=machine_id,
                timestamp=timestamp,
                diagnosis="Unable to parse LLM response — manual inspection recommended",
                recommended_action="Review machine sensor data manually. Contact maintenance supervisor.",
                severity=SeverityLevel.MEDIUM,
                confidence_score=0.3,
                supporting_evidence=[
                    EvidenceItem(
                        description="LLM response could not be parsed as structured JSON",
                        source="pattern",
                    )
                ],
                source="rules_fallback",
                raw_sensor_snapshot=raw_sensor_snapshot,
            )

        # Extract fields with safe defaults
        evidence_raw = parsed.get("supporting_evidence", [])
        evidence = []
        for item in evidence_raw:
            if isinstance(item, dict):
                evidence.append(
                    EvidenceItem(
                        description=item.get("description", ""),
                        source=item.get("source", "pattern"),
                    )
                )

        return DiagnosisResult(
            machine_id=machine_id,
            timestamp=timestamp,
            diagnosis=parsed.get("diagnosis", "Diagnosis unavailable"),
            recommended_action=parsed.get("recommended_action", "Inspect machine manually"),
            severity=_coerce_severity(parsed.get("severity", "medium")),
            confidence_score=_clamp(float(parsed.get("confidence_score", 0.5)), 0.0, 1.0),
            supporting_evidence=evidence,
            source="llm",
            raw_sensor_snapshot=raw_sensor_snapshot,
        )
