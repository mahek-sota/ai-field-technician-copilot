"""
MockLLMClient — returns deterministic canned JSON responses for tests and demos.

Used when settings.USE_MOCK_LLM=True (or in pytest via conftest.py override).
Always returns a valid JSON string that ResponseParser can parse successfully.

The mock inspects the prompt for keywords to vary the response, making it
useful for testing different severity branches.
"""
import json
from app.llm.base import BaseLLMClient

_BEARING_RESPONSE = {
    "diagnosis": "Bearing wear detected due to elevated temperature and rising vibration trend.",
    "recommended_action": "Schedule immediate inspection of motor assembly. Lubricate or replace bearing if wear is confirmed. Monitor temperature for next 2 hours.",
    "severity": "high",
    "confidence_score": 0.83,
    "supporting_evidence": [
        {"description": "Temperature sensor above warning threshold, consistent with bearing friction", "source": "sensor"},
        {"description": "Vibration level trending upward, indicative of bearing degradation", "source": "sensor"},
        {"description": "Recurring temperature error codes over the past 48 hours", "source": "error_code"},
    ],
}

_PRESSURE_RESPONSE = {
    "diagnosis": "Hydraulic seal failure causing critical pressure loss and reduced flow rate.",
    "recommended_action": "Shut down pump immediately. Inspect all seals and o-rings. Replace any damaged seals before restarting.",
    "severity": "critical",
    "confidence_score": 0.91,
    "supporting_evidence": [
        {"description": "Output pressure critically below minimum operating threshold", "source": "sensor"},
        {"description": "Flow rate below critical threshold indicating internal bypass", "source": "sensor"},
        {"description": "SEAL_WARN error codes indicate known seal degradation", "source": "error_code"},
    ],
}

_MOTOR_RESPONSE = {
    "diagnosis": "Motor overload condition detected, likely due to mechanical jam or excessive load.",
    "recommended_action": "Stop machine. Check for mechanical obstruction or jamming. Inspect motor windings and overload relay before restart.",
    "severity": "high",
    "confidence_score": 0.87,
    "supporting_evidence": [
        {"description": "Motor current draw exceeds rated capacity", "source": "sensor"},
        {"description": "Overload error codes present in recent log", "source": "error_code"},
        {"description": "Pattern consistent with progressive mechanical resistance", "source": "pattern"},
    ],
}

_VIBRATION_RESPONSE = {
    "diagnosis": "Rotor imbalance developing, causing above-normal vibration levels.",
    "recommended_action": "Schedule dynamic balancing procedure within 72 hours. Monitor vibration trend daily. Inspect mounting bolts for looseness.",
    "severity": "medium",
    "confidence_score": 0.76,
    "supporting_evidence": [
        {"description": "Vibration sensor above warning threshold", "source": "sensor"},
        {"description": "Imbalance error code detected in recent log", "source": "error_code"},
        {"description": "Vibration pattern consistent with rotational imbalance", "source": "pattern"},
    ],
}

_CRITICAL_RESPONSE = {
    "diagnosis": "Multiple critical sensor thresholds exceeded — imminent failure risk.",
    "recommended_action": "Stop machine immediately. Do not restart without full inspection by qualified technician. Lock out / tag out procedure required.",
    "severity": "critical",
    "confidence_score": 0.95,
    "supporting_evidence": [
        {"description": "Critical threshold exceeded on primary sensor", "source": "sensor"},
        {"description": "Error codes indicate hardware fault", "source": "error_code"},
    ],
}

_HEALTHY_RESPONSE = {
    "diagnosis": "Machine is operating within normal parameters across all sensor readings.",
    "recommended_action": "No immediate action required. Continue scheduled preventive maintenance.",
    "severity": "low",
    "confidence_score": 0.92,
    "supporting_evidence": [
        {"description": "All sensor readings within normal thresholds", "source": "sensor"},
        {"description": "No error codes present", "source": "error_code"},
    ],
}


class MockLLMClient(BaseLLMClient):
    def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "bearing" in prompt_lower or ("vibrat" in prompt_lower and "temp" in prompt_lower):
            payload = _BEARING_RESPONSE
        elif "pressure" in prompt_lower and ("low" in prompt_lower or "seal" in prompt_lower or "fault" in prompt_lower):
            payload = _PRESSURE_RESPONSE
        elif "motor" in prompt_lower and ("overload" in prompt_lower or "current" in prompt_lower):
            payload = _MOTOR_RESPONSE
        elif "vibrat" in prompt_lower and "imbalance" in prompt_lower:
            payload = _VIBRATION_RESPONSE
        elif "critical" in prompt_lower:
            payload = _CRITICAL_RESPONSE
        else:
            payload = _HEALTHY_RESPONSE
        return json.dumps(payload)
