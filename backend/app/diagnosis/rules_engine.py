"""
RulesEngine — deterministic rule evaluation over sensor readings and error codes.

Rules are evaluated in priority order. Each rule returns a RuleMatch or None.
If a rule fires with confidence >= HIGH_CONFIDENCE_THRESHOLD, the pipeline
short-circuits and returns the match without calling the LLM.

Rule structure:
  - condition(raw_data) -> bool
  - diagnosis: str
  - recommended_action: str
  - severity: SeverityLevel
  - confidence: float
  - evidence_description: str
  - evidence_source: str
"""
from dataclasses import dataclass
from typing import List, Optional

from app.schemas.diagnosis import SeverityLevel, EvidenceItem

HIGH_CONFIDENCE_THRESHOLD = 0.85


@dataclass
class RuleMatch:
    diagnosis: str
    recommended_action: str
    severity: SeverityLevel
    confidence: float
    evidence: List[EvidenceItem]


def _sensor_value(sensors: List[dict], name: str) -> Optional[float]:
    for s in sensors:
        if s.get("name", "").lower() == name.lower():
            return s.get("value")
    return None


def _sensor_status(sensors: List[dict], name: str) -> Optional[str]:
    for s in sensors:
        if s.get("name", "").lower() == name.lower():
            return s.get("status", "normal")
    return None


def _has_error(errors: List[str], substring: str) -> bool:
    return any(substring.lower() in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Rule definitions
# Each rule is a callable: (raw_data: dict) -> Optional[RuleMatch]
# ---------------------------------------------------------------------------

def _rule_critical_temperature(raw_data: dict) -> Optional[RuleMatch]:
    sensors = raw_data.get("sensors", [])
    for s in sensors:
        if "temp" in s.get("name", "").lower() and s.get("status") == "critical":
            return RuleMatch(
                diagnosis=f"Critical temperature detected on {s['name']}: {s['value']}{s.get('unit', '')}",
                recommended_action="Shut down machine immediately. Inspect cooling system, lubrication, and ventilation. Do not restart until temperature returns to normal range.",
                severity=SeverityLevel.CRITICAL,
                confidence=0.95,
                evidence=[
                    EvidenceItem(
                        description=f"{s['name']} = {s['value']}{s.get('unit','')} (critical threshold exceeded)",
                        source="sensor",
                    )
                ],
            )
    return None


def _rule_critical_vibration(raw_data: dict) -> Optional[RuleMatch]:
    sensors = raw_data.get("sensors", [])
    for s in sensors:
        if "vibrat" in s.get("name", "").lower() and s.get("status") == "critical":
            return RuleMatch(
                diagnosis=f"Critical vibration level on {s['name']}: {s['value']}{s.get('unit', '')}",
                recommended_action="Stop machine operation. Inspect bearings, mounting bolts, and rotating components for wear or imbalance. Schedule immediate maintenance.",
                severity=SeverityLevel.CRITICAL,
                confidence=0.92,
                evidence=[
                    EvidenceItem(
                        description=f"{s['name']} = {s['value']}{s.get('unit','')} (critical vibration)",
                        source="sensor",
                    )
                ],
            )
    return None


def _rule_low_pressure(raw_data: dict) -> Optional[RuleMatch]:
    sensors = raw_data.get("sensors", [])
    errors = raw_data.get("errors", [])
    for s in sensors:
        if "pressure" in s.get("name", "").lower() and s.get("status") in ("warning", "critical"):
            severity = SeverityLevel.CRITICAL if s.get("status") == "critical" else SeverityLevel.HIGH
            evidence = [
                EvidenceItem(
                    description=f"{s['name']} = {s['value']}{s.get('unit','')} — below threshold",
                    source="sensor",
                )
            ]
            if _has_error(errors, "pressure"):
                evidence.append(EvidenceItem(description="Pressure-related error code in log", source="error_code"))
            return RuleMatch(
                diagnosis=f"Abnormal pressure reading on {s['name']}",
                recommended_action="Check for leaks in the pneumatic/hydraulic circuit. Inspect seals, hoses, and fittings. Verify pump operation.",
                severity=severity,
                confidence=0.88,
                evidence=evidence,
            )
    return None


def _rule_motor_overload_error(raw_data: dict) -> Optional[RuleMatch]:
    errors = raw_data.get("errors", [])
    if _has_error(errors, "overload") or _has_error(errors, "E_MOTOR"):
        return RuleMatch(
            diagnosis="Motor overload condition detected via error code",
            recommended_action="Check motor current draw and load. Inspect for mechanical jam or excessive friction. Reset overload relay after resolving root cause.",
            severity=SeverityLevel.HIGH,
            confidence=0.90,
            evidence=[
                EvidenceItem(
                    description="Motor overload error code present in recent error log",
                    source="error_code",
                )
            ],
        )
    return None


def _rule_offline_no_sensors(raw_data: dict) -> Optional[RuleMatch]:
    sensors = raw_data.get("sensors", [])
    if not sensors:
        return RuleMatch(
            diagnosis="Machine appears offline — no sensor data available",
            recommended_action="Verify network connectivity and PLC communication. Check sensor wiring and data acquisition system.",
            severity=SeverityLevel.HIGH,
            confidence=0.87,
            evidence=[
                EvidenceItem(
                    description="No sensor readings available from machine",
                    source="pattern",
                )
            ],
        )
    return None


def _rule_warning_temperature(raw_data: dict) -> Optional[RuleMatch]:
    sensors = raw_data.get("sensors", [])
    for s in sensors:
        if "temp" in s.get("name", "").lower() and s.get("status") == "warning":
            return RuleMatch(
                diagnosis=f"Elevated temperature warning on {s['name']}: {s['value']}{s.get('unit', '')}",
                recommended_action="Monitor closely. Check cooling system efficiency and airflow. Schedule maintenance inspection within 24 hours.",
                severity=SeverityLevel.MEDIUM,
                confidence=0.80,
                evidence=[
                    EvidenceItem(
                        description=f"{s['name']} = {s['value']}{s.get('unit','')} (warning threshold exceeded)",
                        source="sensor",
                    )
                ],
            )
    return None


def _rule_combined_temp_vibration(raw_data: dict) -> Optional[RuleMatch]:
    """Both temperature and vibration elevated simultaneously → likely bearing failure."""
    sensors = raw_data.get("sensors", [])
    temp_elevated = any(
        "temp" in s.get("name", "").lower() and s.get("status") in ("warning", "critical")
        for s in sensors
    )
    vib_elevated = any(
        "vibrat" in s.get("name", "").lower() and s.get("status") in ("warning", "critical")
        for s in sensors
    )
    if temp_elevated and vib_elevated:
        temp_s = next((s for s in sensors if "temp" in s.get("name", "").lower()), {})
        vib_s = next((s for s in sensors if "vibrat" in s.get("name", "").lower()), {})
        return RuleMatch(
            diagnosis="Bearing wear likely — simultaneous temperature and vibration anomalies detected",
            recommended_action="Inspect motor bearing assembly. Check lubrication levels. Schedule bearing replacement if wear is confirmed.",
            severity=SeverityLevel.HIGH,
            confidence=0.88,
            evidence=[
                EvidenceItem(
                    description=f"{temp_s.get('name','temperature')} = {temp_s.get('value','?')}{temp_s.get('unit','')} (elevated)",
                    source="sensor",
                ),
                EvidenceItem(
                    description=f"{vib_s.get('name','vibration')} = {vib_s.get('value','?')}{vib_s.get('unit','')} (elevated)",
                    source="sensor",
                ),
                EvidenceItem(
                    description="Co-occurring temperature and vibration anomalies are a strong bearing-wear pattern",
                    source="pattern",
                ),
            ],
        )
    return None


def _rule_recurring_errors(raw_data: dict) -> Optional[RuleMatch]:
    """Same error code string appearing 3+ times indicates a systematic fault."""
    errors = raw_data.get("errors", [])
    if len(errors) < 3:
        return None
    # Count occurrences of each first token (error code prefix)
    from collections import Counter
    counts = Counter(str(e).split(":")[0].strip() for e in errors)
    for code, count in counts.most_common(1):
        if count >= 3:
            return RuleMatch(
                diagnosis=f"Systematic fault detected — error '{code}' has occurred {count} times",
                recommended_action="Investigate root cause of recurring fault. Check related subsystem components and wiring. Review maintenance history.",
                severity=SeverityLevel.HIGH,
                confidence=0.82,
                evidence=[
                    EvidenceItem(
                        description=f"Error code '{code}' recurred {count} times — indicates unresolved underlying fault",
                        source="error_code",
                    )
                ],
            )
    return None


def _rule_warning_vibration(raw_data: dict) -> Optional[RuleMatch]:
    sensors = raw_data.get("sensors", [])
    for s in sensors:
        if "vibrat" in s.get("name", "").lower() and s.get("status") == "warning":
            return RuleMatch(
                diagnosis=f"Above-normal vibration on {s['name']}: {s['value']}{s.get('unit', '')} — possible imbalance or bearing wear",
                recommended_action="Inspect rotating components for imbalance or bearing wear. Check mounting bolts. Schedule balancing if imbalance is confirmed.",
                severity=SeverityLevel.MEDIUM,
                confidence=0.78,
                evidence=[
                    EvidenceItem(
                        description=f"{s['name']} = {s['value']}{s.get('unit','')} (above warning threshold)",
                        source="sensor",
                    )
                ],
            )
    return None


# Ordered list — evaluated top to bottom; first high-confidence match short-circuits LLM
RULES = [
    _rule_offline_no_sensors,
    _rule_critical_temperature,
    _rule_critical_vibration,
    _rule_combined_temp_vibration,
    _rule_motor_overload_error,
    _rule_low_pressure,
    _rule_recurring_errors,
    _rule_warning_temperature,
    _rule_warning_vibration,
]


class RulesEngine:
    def evaluate(self, raw_data: dict) -> Optional[RuleMatch]:
        """
        Evaluate all rules in order. Return the first match whose confidence
        meets or exceeds HIGH_CONFIDENCE_THRESHOLD. Returns None if no rule fires
        at high confidence (signals: proceed to LLM).
        """
        for rule_fn in RULES:
            match = rule_fn(raw_data)
            if match is not None and match.confidence >= HIGH_CONFIDENCE_THRESHOLD:
                return match
        return None

    def evaluate_all(self, raw_data: dict) -> List[RuleMatch]:
        """Return all matches regardless of confidence (used to build LLM context)."""
        matches = []
        for rule_fn in RULES:
            match = rule_fn(raw_data)
            if match is not None:
                matches.append(match)
        return matches
